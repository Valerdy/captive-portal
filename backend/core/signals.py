"""
Signals for automatic synchronization:
- Role synchronization with Django permissions
- Profile change tracking
- RADIUS + MikroTik synchronization

Ce module gère:
- Synchronisation utilisateur → RADIUS + MikroTik lors des changements
- Synchronisation profil → MikroTik lors des modifications
- Synchronisation promotion → tous les utilisateurs lors des changements
"""
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from contextlib import contextmanager
import threading
import logging

from .models import User, Profile, Promotion, ProfileHistory, UserProfileUsage

logger = logging.getLogger(__name__)


# =============================================================================
# Thread-safe synchronization flag
# =============================================================================
# Utilise threading.local() pour éviter les race conditions en environnement
# multi-thread (Gunicorn, uWSGI). Chaque thread a sa propre copie du flag.

_sync_state = threading.local()


def get_sync_enabled() -> bool:
    """Vérifie si la synchronisation automatique est activée."""
    return getattr(settings, 'PROFILE_AUTO_SYNC', True)


def set_syncing(value: bool):
    """Active/désactive le flag de synchronisation (thread-safe)."""
    _sync_state.syncing = value


def is_syncing() -> bool:
    """Vérifie si une synchronisation est en cours (thread-safe)."""
    return getattr(_sync_state, 'syncing', False)


@contextmanager
def sync_context():
    """
    Context manager pour la synchronisation thread-safe.

    Usage:
        with sync_context():
            # Code de synchronisation
            pass
    """
    try:
        set_syncing(True)
        yield
    finally:
        set_syncing(False)


# =============================================================================
# User Role Synchronization
# =============================================================================

@receiver(pre_save, sender=User)
def sync_role_with_permissions(sender, instance, **kwargs):
    """
    Synchronize user role with is_staff and is_superuser flags.

    Priority:
    1. is_staff=True or is_superuser=True → admin role
    2. Otherwise → user role
    """
    if instance.is_staff or instance.is_superuser:
        instance.role = 'admin'
    elif not instance.role or instance.role == 'admin':
        instance.role = 'user'


# =============================================================================
# Profile Change Tracking
# =============================================================================

@receiver(pre_save, sender=User)
def track_user_changes(sender, instance, **kwargs):
    """
    Track profile, promotion, and status changes before saving User model.
    """
    if instance.pk:
        try:
            old_instance = User.objects.get(pk=instance.pk)
            instance._old_profile_id = old_instance.profile_id
            instance._old_promotion_id = old_instance.promotion_id
            instance._old_is_radius_enabled = old_instance.is_radius_enabled
            instance._old_is_active = old_instance.is_active
        except User.DoesNotExist:
            instance._old_profile_id = None
            instance._old_promotion_id = None
            instance._old_is_radius_enabled = None
            instance._old_is_active = None
    else:
        instance._old_profile_id = None
        instance._old_promotion_id = None
        instance._old_is_radius_enabled = None
        instance._old_is_active = None


@receiver(post_save, sender=User)
def handle_user_profile_change(sender, instance, created, **kwargs):
    """
    Create ProfileHistory entry and manage UserProfileUsage after User is saved.
    """
    if created and not instance.profile:
        return

    old_profile_id = getattr(instance, '_old_profile_id', None)
    new_profile_id = instance.profile_id if instance.profile else None

    if old_profile_id != new_profile_id:
        if old_profile_id is None and new_profile_id is not None:
            change_type = 'assigned'
        elif old_profile_id is not None and new_profile_id is None:
            change_type = 'removed'
        elif old_profile_id is not None and new_profile_id is not None:
            change_type = 'updated'
        else:
            return

        ProfileHistory.objects.create(
            user=instance,
            old_profile_id=old_profile_id,
            new_profile_id=new_profile_id,
            change_type=change_type,
            reason=f"Profil automatiquement modifié ({change_type})"
        )

        if new_profile_id is not None:
            usage, usage_created = UserProfileUsage.objects.get_or_create(
                user=instance,
                defaults={'is_active': True}
            )
            if not usage_created and change_type == 'updated':
                usage.reset_all()
        elif new_profile_id is None:
            try:
                usage = UserProfileUsage.objects.get(user=instance)
                usage.is_active = False
                usage.save()
            except UserProfileUsage.DoesNotExist:
                pass


@receiver(post_save, sender=User)
def ensure_profile_usage_exists(sender, instance, created, **kwargs):
    """
    Ensure UserProfileUsage exists for users with profiles.
    """
    if instance.profile or (instance.promotion and instance.promotion.profile):
        UserProfileUsage.objects.get_or_create(
            user=instance,
            defaults={'is_active': True}
        )


# =============================================================================
# RADIUS + MikroTik Synchronization for Users
# =============================================================================

@receiver(post_save, sender=User)
def sync_user_to_radius_and_mikrotik(sender, instance, created, **kwargs):
    """
    Synchronise l'utilisateur avec RADIUS (attributs + groupe) et MikroTik.

    Architecture RADIUS-based:
    - radcheck: credentials (Cleartext-Password)
    - radreply: attributs individuels (si nécessaire)
    - radusergroup: association au groupe du profil (profile_{id}_{name})

    Gère:
    - Changement de profil individuel
    - Changement de promotion
    - Changement de statut is_radius_enabled
    """
    if is_syncing() or not get_sync_enabled():
        return

    # Ne pas synchroniser les nouveaux utilisateurs (gérés par le endpoint register)
    if created:
        logger.debug(f"User '{instance.username}' created - sync handled by registration")
        return

    # Vérifier si l'utilisateur est activé dans RADIUS
    if not instance.is_radius_activated:
        return

    # Détecter les changements
    old_profile_id = getattr(instance, '_old_profile_id', None)
    old_promotion_id = getattr(instance, '_old_promotion_id', None)
    old_is_radius_enabled = getattr(instance, '_old_is_radius_enabled', None)
    old_is_active = getattr(instance, '_old_is_active', None)

    profile_changed = old_profile_id != instance.profile_id
    promotion_changed = old_promotion_id != instance.promotion_id
    status_changed = old_is_radius_enabled != instance.is_radius_enabled
    active_changed = old_is_active != instance.is_active

    if not (profile_changed or promotion_changed or status_changed or active_changed):
        return

    try:
        set_syncing(True)

        from radius.services import ProfileRadiusService, RadiusProfileGroupService

        # Gestion de la désactivation/réactivation
        if status_changed or active_changed:
            if instance.is_radius_enabled and instance.is_active:
                ProfileRadiusService.reactivate_user_radius(instance)
                logger.info(f"User '{instance.username}' reactivated in RADIUS")
            else:
                ProfileRadiusService.deactivate_user_radius(instance, reason='manual')
                logger.info(f"User '{instance.username}' deactivated in RADIUS")

        # Gestion du changement de profil/promotion
        if (profile_changed or promotion_changed) and instance.is_radius_enabled:
            # Sync attributs individuels (legacy)
            ProfileRadiusService.sync_user_to_radius(instance)

            # Sync groupe RADIUS (nouvelle architecture)
            group_result = RadiusProfileGroupService.sync_user_profile_group(instance)
            if group_result.get('groupname'):
                logger.info(
                    f"👤 User '{instance.username}' assigné au groupe "
                    f"'{group_result['groupname']}' (source: {group_result.get('source', 'unknown')})"
                )
            else:
                logger.info(f"User '{instance.username}' synced with new profile")

        # Synchroniser avec MikroTik (optionnel)
        if getattr(settings, 'MIKROTIK_SYNC_ENABLED', True):
            try:
                from mikrotik.profile_service import MikrotikProfileSyncService
                mikrotik_service = MikrotikProfileSyncService()

                if mikrotik_service.router:
                    if status_changed or active_changed:
                        if instance.is_radius_enabled and instance.is_active:
                            mikrotik_service.enable_hotspot_user(instance.username)
                        else:
                            mikrotik_service.disable_hotspot_user(instance.username)
                    elif profile_changed or promotion_changed:
                        mikrotik_service.sync_user(instance)

            except Exception as e:
                logger.warning(f"MikroTik sync failed for '{instance.username}': {e}")

    except Exception as e:
        logger.error(f"Error syncing user '{instance.username}': {e}")
    finally:
        set_syncing(False)


@receiver(post_delete, sender=User)
def remove_user_from_radius_and_mikrotik(sender, instance, **kwargs):
    """
    Supprime l'utilisateur de RADIUS (credentials + groupes) et MikroTik.
    """
    if is_syncing() or not get_sync_enabled():
        return

    try:
        set_syncing(True)

        from radius.models import RadCheck, RadReply, RadUserGroup

        # Supprimer toutes les entrées RADIUS pour cet utilisateur
        deleted_check = RadCheck.objects.filter(username=instance.username).delete()[0]
        deleted_reply = RadReply.objects.filter(username=instance.username).delete()[0]
        deleted_groups = RadUserGroup.objects.filter(username=instance.username).delete()[0]

        logger.info(
            f"🗑️ User '{instance.username}' removed from RADIUS: "
            f"{deleted_check} check, {deleted_reply} reply, {deleted_groups} groups"
        )

        # Supprimer de MikroTik (optionnel)
        if getattr(settings, 'MIKROTIK_SYNC_ENABLED', True):
            try:
                from mikrotik.profile_service import MikrotikProfileSyncService
                mikrotik_service = MikrotikProfileSyncService()
                if mikrotik_service.router:
                    mikrotik_service.delete_hotspot_user(instance.username)
            except Exception as e:
                logger.warning(f"MikroTik delete failed for '{instance.username}': {e}")

    except Exception as e:
        logger.error(f"Error deleting user '{instance.username}' from RADIUS: {e}")
    finally:
        set_syncing(False)


# =============================================================================
# Profile Synchronization to RADIUS Groups (+ MikroTik optionnel)
# =============================================================================

@receiver(post_save, sender=Profile)
def sync_profile_to_radius_group(sender, instance, created, **kwargs):
    """
    Synchronise le profil vers un groupe FreeRADIUS après création/modification.

    Architecture RADIUS-based:
    - Chaque Profile = un groupe FreeRADIUS (profile_{id}_{name})
    - Les attributs sont écrits dans radgroupreply/radgroupcheck
    - Les utilisateurs héritent via radusergroup

    Note: Ce signal ne lève jamais d'exception pour ne pas bloquer
    la sauvegarde du profil dans Django.
    """
    try:
        if is_syncing() or not get_sync_enabled():
            return

        set_syncing(True)

        # =====================================================================
        # Synchronisation RADIUS (OBLIGATOIRE)
        # =====================================================================
        from radius.services import RadiusProfileGroupService

        result = RadiusProfileGroupService.sync_profile_to_radius_group(instance)

        if result.get('success'):
            action = 'créé' if created else 'mis à jour'
            logger.info(
                f"✅ Profil '{instance.name}' {action} dans RADIUS groupe "
                f"'{result.get('groupname')}': {result.get('reply_attributes')} attrs"
            )
        else:
            logger.warning(f"Échec sync profil '{instance.name}' vers RADIUS")

        # =====================================================================
        # Synchronisation MikroTik (OPTIONNELLE)
        # =====================================================================
        if getattr(settings, 'MIKROTIK_SYNC_ENABLED', True):
            try:
                from mikrotik.profile_service import MikrotikProfileSyncService
                mikrotik_service = MikrotikProfileSyncService()

                if mikrotik_service.router:
                    mt_result = mikrotik_service.sync_profile(instance)
                    if mt_result.get('success'):
                        logger.info(f"Profil '{instance.name}' synchronisé vers MikroTik")

                        # Si modification, mettre à jour les utilisateurs MikroTik
                        if not created:
                            sync_users_with_profile_change(instance, mikrotik_service)

            except Exception as e:
                logger.warning(f"MikroTik sync failed for profile '{instance.name}': {e}")

    except Exception as e:
        logger.error(f"Error syncing profile '{instance.name}': {e}", exc_info=True)
    finally:
        try:
            set_syncing(False)
        except Exception:
            pass


def sync_users_with_profile_change(profile, mikrotik_service):
    """
    Synchronise tous les utilisateurs utilisant un profil donné.
    """
    from radius.services import ProfileRadiusService

    # Utilisateurs avec ce profil individuel
    direct_users = User.objects.filter(
        profile=profile,
        is_radius_activated=True,
        is_active=True
    )

    # Utilisateurs via promotion (sans profil individuel)
    promotion_users = User.objects.filter(
        promotion__profile=profile,
        profile__isnull=True,
        is_radius_activated=True,
        is_active=True
    )

    all_users = list(direct_users) + list(promotion_users)

    for user in all_users:
        try:
            ProfileRadiusService.sync_user_to_radius(user, profile)
            mikrotik_service.sync_user(user)
        except Exception as e:
            logger.warning(f"Failed to sync user '{user.username}' after profile change: {e}")


@receiver(post_delete, sender=Profile)
def remove_profile_from_radius_group(sender, instance, **kwargs):
    """
    Supprime le groupe RADIUS et optionnellement le profil MikroTik.

    Note: Ce signal ne doit JAMAIS lever d'exception pour éviter de bloquer
    la suppression du profil dans Django. Toutes les erreurs sont loguées
    mais n'empêchent pas la transaction.
    """
    try:
        if is_syncing() or not get_sync_enabled():
            return

        set_syncing(True)

        # =====================================================================
        # Suppression groupe RADIUS (OBLIGATOIRE)
        # =====================================================================
        from radius.services import RadiusProfileGroupService

        result = RadiusProfileGroupService.remove_profile_from_radius_group(instance)

        if result.get('success'):
            logger.info(
                f"🗑️ Profil '{instance.name}' supprimé de RADIUS: "
                f"{result.get('deleted_usergroup', 0)} utilisateurs affectés"
            )

        # =====================================================================
        # Suppression MikroTik (OPTIONNELLE)
        # =====================================================================
        if getattr(settings, 'MIKROTIK_SYNC_ENABLED', True):
            try:
                from mikrotik.profile_service import MikrotikProfileSyncService
                mikrotik_service = MikrotikProfileSyncService()

                if mikrotik_service.router:
                    profile_name = mikrotik_service._get_mikrotik_profile_name(instance)
                    mt_result = mikrotik_service.delete_hotspot_profile(profile_name)

                    if mt_result.get('success'):
                        logger.info(f"Profil '{instance.name}' supprimé de MikroTik")

            except Exception as e:
                logger.warning(f"MikroTik delete failed for profile '{instance.name}': {e}")

    except Exception as e:
        logger.error(f"Error deleting profile '{instance.name}': {e}", exc_info=True)
    finally:
        try:
            set_syncing(False)
        except Exception:
            pass


# =============================================================================
# Promotion Synchronization
# =============================================================================

@receiver(pre_save, sender=Promotion)
def track_promotion_changes(sender, instance, **kwargs):
    """
    Capture l'état de la promotion avant la sauvegarde.
    """
    if instance.pk:
        try:
            old_instance = Promotion.objects.get(pk=instance.pk)
            instance._old_profile_id = old_instance.profile_id
            instance._old_is_active = old_instance.is_active
        except Promotion.DoesNotExist:
            instance._old_profile_id = None
            instance._old_is_active = None
    else:
        instance._old_profile_id = None
        instance._old_is_active = None


@receiver(post_save, sender=Promotion)
def sync_promotion_users(sender, instance, created, **kwargs):
    """
    Synchronise les utilisateurs de la promotion après modification du profil.

    Quand le profil d'une promotion change:
    1. Sync attributs RADIUS individuels (legacy)
    2. Reassigne les utilisateurs au nouveau groupe RADIUS
    """
    if is_syncing() or not get_sync_enabled():
        return

    if created:
        return

    old_profile_id = getattr(instance, '_old_profile_id', None)
    old_is_active = getattr(instance, '_old_is_active', None)

    profile_changed = old_profile_id != instance.profile_id
    status_changed = old_is_active != instance.is_active

    if not (profile_changed or status_changed):
        return

    try:
        set_syncing(True)

        from radius.services import PromotionRadiusService, RadiusProfileGroupService

        if status_changed and not instance.is_active:
            result = PromotionRadiusService.deactivate_promotion(
                instance,
                reason='promotion_disabled'
            )
            logger.info(f"Promotion '{instance.name}' deactivated: {result.get('deactivated', 0)} users")

        elif profile_changed and instance.profile:
            # Sync attributs individuels (legacy)
            result = PromotionRadiusService.sync_promotion_users(instance)
            logger.info(f"Promotion '{instance.name}' profile changed: {result.get('synced', 0)} users synced")

            # Sync groupes RADIUS pour tous les utilisateurs de la promotion
            # (uniquement ceux sans profil individuel)
            users = instance.users.filter(
                is_radius_activated=True,
                is_active=True,
                profile__isnull=True  # Sans profil direct
            )

            group_synced = 0
            for user in users:
                try:
                    group_result = RadiusProfileGroupService.sync_user_profile_group(user)
                    if group_result.get('groupname'):
                        group_synced += 1
                except Exception as e:
                    logger.warning(f"Failed to sync group for '{user.username}': {e}")

            logger.info(
                f"👥 Promotion '{instance.name}': {group_synced} utilisateurs "
                f"reassignés au groupe '{RadiusProfileGroupService.get_group_name(instance.profile)}'"
            )

            # MikroTik sync (optionnel)
            if getattr(settings, 'MIKROTIK_SYNC_ENABLED', True):
                try:
                    from mikrotik.profile_service import MikrotikProfileSyncService
                    mikrotik_service = MikrotikProfileSyncService()
                    if mikrotik_service.router:
                        mikrotik_service.sync_promotion_users(instance)
                except Exception as e:
                    logger.warning(f"MikroTik sync failed for promotion '{instance.name}': {e}")

    except Exception as e:
        logger.error(f"Error syncing promotion '{instance.name}': {e}")
    finally:
        set_syncing(False)


# =============================================================================
# Utilitaires
# =============================================================================

def sync_all_to_radius_groups():
    """
    Utilitaire pour synchroniser tous les profils et utilisateurs vers RADIUS groups.
    À utiliser après migration initiale vers l'architecture group-based.

    Returns:
        Dict avec les résultats de synchronisation
    """
    from radius.services import RadiusProfileGroupService

    logger.info("=" * 70)
    logger.info("SYNCHRONISATION COMPLÈTE VERS RADIUS GROUPS")
    logger.info("=" * 70)

    results = {
        'profiles': None,
        'users': None
    }

    # Étape 1: Synchroniser tous les profils vers des groupes RADIUS
    logger.info("\n[1/2] Synchronisation des profils vers radgroupreply/radgroupcheck...")
    results['profiles'] = RadiusProfileGroupService.sync_all_profiles_to_groups()

    # Étape 2: Synchroniser tous les utilisateurs vers leurs groupes
    logger.info("\n[2/2] Assignation des utilisateurs à leurs groupes de profil...")
    results['users'] = RadiusProfileGroupService.sync_all_users_to_groups()

    logger.info("\n" + "=" * 70)
    logger.info("SYNCHRONISATION TERMINÉE")
    logger.info(f"Profils: {results['profiles'].get('success', 0)}/{results['profiles'].get('total', 0)}")
    logger.info(f"Utilisateurs: {results['users'].get('assigned', 0)}/{results['users'].get('total', 0)}")
    logger.info("=" * 70)

    return results


def sync_all_to_radius_and_mikrotik():
    """
    Utilitaire pour synchroniser tous les profils et utilisateurs.
    Inclut RADIUS groups + MikroTik.
    """
    logger.info("Starting full sync to RADIUS groups and MikroTik...")

    # Sync RADIUS groups
    radius_results = sync_all_to_radius_groups()

    # Sync MikroTik (optionnel)
    mikrotik_results = None
    if getattr(settings, 'MIKROTIK_SYNC_ENABLED', True):
        try:
            from mikrotik.profile_service import FullProfileSyncService
            service = FullProfileSyncService()
            mikrotik_results = service.sync_all()
        except Exception as e:
            logger.warning(f"MikroTik sync failed: {e}")

    return {
        'radius': radius_results,
        'mikrotik': mikrotik_results
    }

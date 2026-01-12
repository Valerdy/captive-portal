"""
Signals for automatic synchronization:
- Role synchronization with Django permissions
- Profile change tracking
- RADIUS + MikroTik synchronization

Ce module gère:
- Synchronisation utilisateur → RADIUS + MikroTik lors des changements
- Synchronisation profil → MikroTik lors des modifications
- Synchronisation promotion → tous les utilisateurs lors des changements

Fixes appliqués:
- #4: Nettoyage complet RADIUS à la suppression utilisateur
- #7: Gestion exceptions avec logging SyncFailureLog
- #12: Gestion RADIUS OK mais MikroTik KO
- #14: Race condition historique profil avec select_for_update
"""
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from django.db import transaction
from contextlib import contextmanager
import threading
import logging
import traceback

from .models import User, Profile, Promotion, ProfileHistory, UserProfileUsage, BlockedSite

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


def log_sync_failure(sync_type, source, error, context=None):
    """
    Enregistre un échec de synchronisation.
    Fix #7: Traçabilité des erreurs pour retry et alertes.
    """
    try:
        from .models import SyncFailureLog
        SyncFailureLog.log_failure(
            sync_type=sync_type,
            source=source,
            error=error,
            context=context,
            traceback_str=traceback.format_exc()
        )
    except Exception as e:
        # Ne jamais bloquer le flux principal pour le logging
        logger.error(f"Failed to log sync failure: {e}")


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
# Profile Change Tracking (Fix #14: Race Condition)
# =============================================================================

@receiver(pre_save, sender=User)
def track_user_changes(sender, instance, **kwargs):
    """
    Track profile, promotion, and status changes before saving User model.

    Fix #14: Utilise select_for_update pour éviter les race conditions
    lors de la lecture de l'état précédent.
    """
    if instance.pk:
        try:
            # Fix #14: Verrouillage pour éviter race condition
            with transaction.atomic():
                old_instance = User.objects.select_for_update(nowait=False).filter(
                    pk=instance.pk
                ).values(
                    'profile_id', 'promotion_id', 'is_radius_enabled', 'is_active'
                ).first()

                if old_instance:
                    instance._old_profile_id = old_instance['profile_id']
                    instance._old_promotion_id = old_instance['promotion_id']
                    instance._old_is_radius_enabled = old_instance['is_radius_enabled']
                    instance._old_is_active = old_instance['is_active']
                else:
                    _set_old_values_to_none(instance)
        except Exception as e:
            # En cas d'erreur, on continue sans tracking
            logger.warning(f"Failed to track user changes: {e}")
            _set_old_values_to_none(instance)
    else:
        _set_old_values_to_none(instance)


def _set_old_values_to_none(instance):
    """Helper pour initialiser les valeurs tracking à None."""
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
# RADIUS + MikroTik Synchronization for Users (Fix #7, #12)
# =============================================================================

@receiver(post_save, sender=User)
def sync_user_to_radius_and_mikrotik(sender, instance, created, **kwargs):
    """
    Synchronise l'utilisateur avec RADIUS (attributs + groupe) et MikroTik.

    Architecture RADIUS-based:
    - radcheck: credentials (Cleartext-Password)
    - radreply: attributs individuels (si nécessaire)
    - radusergroup: association au groupe du profil (profile_{id}_{name})

    Fix #7: Logging des erreurs avec SyncFailureLog
    Fix #12: Gestion séparée RADIUS/MikroTik avec tracking d'état
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

    sync_results = {
        'radius_success': False,
        'mikrotik_success': False,
        'radius_error': None,
        'mikrotik_error': None
    }

    try:
        set_syncing(True)

        from radius.services import ProfileRadiusService, RadiusProfileGroupService

        # === ÉTAPE 1: Synchronisation RADIUS ===
        try:
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

            sync_results['radius_success'] = True

        except Exception as e:
            sync_results['radius_error'] = str(e)
            logger.error(f"RADIUS sync failed for '{instance.username}': {e}")
            # Fix #7: Log l'échec pour retry ultérieur
            log_sync_failure('radius_user', instance, e, {
                'profile_changed': profile_changed,
                'promotion_changed': promotion_changed,
                'status_changed': status_changed
            })

        # === ÉTAPE 2: Synchronisation MikroTik (Fix #12: indépendante de RADIUS) ===
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

                    sync_results['mikrotik_success'] = True

            except Exception as e:
                sync_results['mikrotik_error'] = str(e)
                logger.warning(f"MikroTik sync failed for '{instance.username}': {e}")
                # Fix #7 & #12: Log l'échec MikroTik séparément
                log_sync_failure('mikrotik_user', instance, e, {
                    'radius_success': sync_results['radius_success']
                })

        # Log le résultat global
        if sync_results['radius_success'] and not sync_results['mikrotik_success']:
            logger.warning(
                f"⚠️ User '{instance.username}': RADIUS OK, MikroTik FAILED - "
                f"État partiel, retry programmé"
            )

    except Exception as e:
        logger.error(f"Error syncing user '{instance.username}': {e}")
    finally:
        set_syncing(False)


@receiver(post_delete, sender=User)
def remove_user_from_radius_and_mikrotik(sender, instance, **kwargs):
    """
    Supprime l'utilisateur de RADIUS (credentials + groupes) et MikroTik.

    Fix #4: Nettoyage COMPLET de toutes les tables RADIUS:
    - radcheck (credentials)
    - radreply (attributs)
    - radusergroup (associations groupes)
    - radpostauth (historique auth - optionnel)
    - radacct (sessions - conservé pour historique)
    """
    if is_syncing() or not get_sync_enabled():
        return

    username = instance.username
    cleanup_results = {
        'radcheck': 0,
        'radreply': 0,
        'radusergroup': 0,
        'radpostauth': 0,
        'mikrotik': False,
        'errors': []
    }

    try:
        set_syncing(True)

        from radius.models import RadCheck, RadReply, RadUserGroup

        # Fix #4: Nettoyage COMPLET de toutes les entrées RADIUS
        with transaction.atomic():
            # 1. Supprimer radcheck (credentials)
            cleanup_results['radcheck'] = RadCheck.objects.filter(
                username=username
            ).delete()[0]

            # 2. Supprimer radreply (attributs)
            cleanup_results['radreply'] = RadReply.objects.filter(
                username=username
            ).delete()[0]

            # 3. Supprimer radusergroup (associations aux groupes)
            cleanup_results['radusergroup'] = RadUserGroup.objects.filter(
                username=username
            ).delete()[0]

            # 4. Supprimer radpostauth (historique - optionnel, peut être volumineux)
            try:
                from radius.models import RadPostAuth
                cleanup_results['radpostauth'] = RadPostAuth.objects.filter(
                    username=username
                ).delete()[0]
            except Exception:
                # Table peut ne pas exister ou ne pas être gérée
                pass

        logger.info(
            f"🗑️ User '{username}' removed from RADIUS: "
            f"{cleanup_results['radcheck']} check, "
            f"{cleanup_results['radreply']} reply, "
            f"{cleanup_results['radusergroup']} groups, "
            f"{cleanup_results['radpostauth']} postauth"
        )

        # Supprimer de MikroTik (optionnel)
        if getattr(settings, 'MIKROTIK_SYNC_ENABLED', True):
            try:
                from mikrotik.profile_service import MikrotikProfileSyncService
                mikrotik_service = MikrotikProfileSyncService()
                if mikrotik_service.router:
                    mikrotik_service.delete_hotspot_user(username)
                    cleanup_results['mikrotik'] = True
                    logger.info(f"User '{username}' removed from MikroTik")
            except Exception as e:
                cleanup_results['errors'].append(f"MikroTik: {e}")
                logger.warning(f"MikroTik delete failed for '{username}': {e}")

    except Exception as e:
        cleanup_results['errors'].append(f"RADIUS: {e}")
        logger.error(f"Error deleting user '{username}' from RADIUS: {e}")
    finally:
        set_syncing(False)


# =============================================================================
# Profile Synchronization to RADIUS Groups (+ MikroTik optionnel) - Fix #7, #12
# =============================================================================

@receiver(post_save, sender=Profile)
def sync_profile_to_radius_group(sender, instance, created, **kwargs):
    """
    Synchronise le profil vers FreeRADIUS selon l'Option C (contrôle manuel).

    Fix #7: Logging des erreurs avec SyncFailureLog
    Fix #12: Gestion séparée RADIUS/MikroTik
    """
    try:
        if is_syncing() or not get_sync_enabled():
            return

        set_syncing(True)

        from radius.services import RadiusProfileGroupService
        from django.utils import timezone

        sync_results = {
            'radius_success': False,
            'mikrotik_success': False
        }

        # =====================================================================
        # OPTION C: Sync contrôlée par is_radius_enabled
        # =====================================================================

        if instance.can_sync_to_radius():
            # === Synchronisation RADIUS ===
            try:
                result = RadiusProfileGroupService.sync_profile_to_radius_group(instance)

                if result.get('success'):
                    action = 'créé' if created else 'mis à jour'
                    logger.info(
                        f"✅ Profil '{instance.name}' {action} dans RADIUS groupe "
                        f"'{result.get('groupname')}': {result.get('reply_attributes')} attrs"
                    )

                    # Mettre à jour les métadonnées (sans déclencher le signal)
                    Profile.objects.filter(pk=instance.pk).update(
                        radius_group_name=result.get('groupname'),
                        last_radius_sync=timezone.now()
                    )
                    sync_results['radius_success'] = True
                else:
                    logger.warning(f"Échec sync profil '{instance.name}' vers RADIUS")
                    log_sync_failure('radius_profile', instance, "Sync returned failure", {
                        'result': result
                    })

            except Exception as e:
                logger.error(f"RADIUS sync failed for profile '{instance.name}': {e}")
                log_sync_failure('radius_profile', instance, e)

            # === Synchronisation MikroTik (Fix #12: indépendante) ===
            if getattr(settings, 'MIKROTIK_SYNC_ENABLED', True):
                try:
                    from mikrotik.profile_service import MikrotikProfileSyncService
                    mikrotik_service = MikrotikProfileSyncService()

                    if mikrotik_service.router:
                        mt_result = mikrotik_service.sync_profile(instance)
                        if mt_result.get('success'):
                            logger.info(f"Profil '{instance.name}' synchronisé vers MikroTik")
                            sync_results['mikrotik_success'] = True

                            # Si modification, mettre à jour les utilisateurs MikroTik
                            if not created:
                                sync_users_with_profile_change(instance, mikrotik_service)

                except Exception as e:
                    logger.warning(f"MikroTik sync failed for profile '{instance.name}': {e}")
                    log_sync_failure('mikrotik_profile', instance, e, {
                        'radius_success': sync_results['radius_success']
                    })

            # Log état partiel
            if sync_results['radius_success'] and not sync_results['mikrotik_success']:
                logger.warning(
                    f"⚠️ Profile '{instance.name}': RADIUS OK, MikroTik FAILED"
                )

        elif instance.is_synced_to_radius:
            # Était synchronisé mais ne devrait plus l'être → Supprimer
            try:
                result = RadiusProfileGroupService.remove_profile_from_radius_group(instance)

                if result.get('success'):
                    logger.info(f"🗑️ Profil '{instance.name}' supprimé de RADIUS")

                    # Nettoyer les métadonnées
                    Profile.objects.filter(pk=instance.pk).update(
                        radius_group_name=None,
                        last_radius_sync=None
                    )
            except Exception as e:
                logger.error(f"Failed to remove profile '{instance.name}' from RADIUS: {e}")
                log_sync_failure('radius_profile', instance, e, {'action': 'remove'})

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
            log_sync_failure('radius_user', user, e, {'trigger': 'profile_change'})


@receiver(post_delete, sender=Profile)
def remove_profile_from_radius_group(sender, instance, **kwargs):
    """
    Supprime le groupe RADIUS et optionnellement le profil MikroTik.

    Fix #5: Cascade vers RADIUS et MikroTik
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
                log_sync_failure('mikrotik_profile', instance, e, {'action': 'delete'})

    except Exception as e:
        logger.error(f"Error deleting profile '{instance.name}': {e}", exc_info=True)
    finally:
        try:
            set_syncing(False)
        except Exception:
            pass


# =============================================================================
# Promotion Synchronization (Fix #14: Race Condition)
# =============================================================================

@receiver(pre_save, sender=Promotion)
def track_promotion_changes(sender, instance, **kwargs):
    """
    Capture l'état de la promotion avant la sauvegarde.

    Fix #14: Utilise select_for_update pour éviter race conditions.
    """
    if instance.pk:
        try:
            with transaction.atomic():
                old_data = Promotion.objects.select_for_update(nowait=False).filter(
                    pk=instance.pk
                ).values('profile_id', 'is_active').first()

                if old_data:
                    instance._old_profile_id = old_data['profile_id']
                    instance._old_is_active = old_data['is_active']
                else:
                    instance._old_profile_id = None
                    instance._old_is_active = None
        except Exception as e:
            logger.warning(f"Failed to track promotion changes: {e}")
            instance._old_profile_id = None
            instance._old_is_active = None
    else:
        instance._old_profile_id = None
        instance._old_is_active = None


@receiver(post_save, sender=Promotion)
def sync_promotion_users(sender, instance, created, **kwargs):
    """
    Synchronise les utilisateurs de la promotion après modification du profil.
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
            users = instance.users.filter(
                is_radius_activated=True,
                is_active=True,
                profile__isnull=True
            )

            group_synced = 0
            for user in users:
                try:
                    group_result = RadiusProfileGroupService.sync_user_profile_group(user)
                    if group_result.get('groupname'):
                        group_synced += 1
                except Exception as e:
                    logger.warning(f"Failed to sync group for '{user.username}': {e}")
                    log_sync_failure('radius_group', user, e, {'promotion': instance.name})

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
                    log_sync_failure('mikrotik_user', instance, e, {'action': 'promotion_sync'})

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


def get_pending_sync_failures():
    """
    Récupère les échecs de sync en attente de retry.

    Returns:
        QuerySet des SyncFailureLog en attente
    """
    from django.utils import timezone
    from .models import SyncFailureLog

    return SyncFailureLog.objects.filter(
        status='pending',
        next_retry_at__lte=timezone.now()
    ).order_by('next_retry_at')


def retry_pending_syncs():
    """
    Retente les synchronisations en échec.
    À appeler via un job périodique (Celery, cron, etc.)

    Returns:
        Dict avec les résultats des retries
    """
    from .models import SyncFailureLog

    results = {
        'retried': 0,
        'success': 0,
        'failed': 0,
        'errors': []
    }

    pending = get_pending_sync_failures()

    for failure in pending:
        results['retried'] += 1
        failure.status = 'retrying'
        failure.save()

        try:
            # TODO: Implémenter la logique de retry selon sync_type
            # Pour l'instant, on programme un nouveau retry
            if failure.schedule_retry():
                results['failed'] += 1
            else:
                results['failed'] += 1
        except Exception as e:
            results['errors'].append(str(e))
            failure.schedule_retry()

    return results


# =============================================================================
# BlockedSite DNS Synchronization
# =============================================================================

@receiver(post_save, sender=BlockedSite)
def sync_blocked_site_to_mikrotik(sender, instance, created, **kwargs):
    """
    Synchronise un BlockedSite vers MikroTik DNS après création/modification.

    Cette fonction est un filet de sécurité pour les modifications effectuées
    en dehors de l'API (admin Django, management commands, etc.).

    Le ViewSet gère déjà la synchronisation pour les requêtes API.
    """
    if is_syncing() or not get_sync_enabled():
        return

    # Ne synchroniser que les blacklist actifs
    if instance.type != 'blacklist':
        return

    # Vérifier si MikroTik est activé
    if not getattr(settings, 'MIKROTIK_SYNC_ENABLED', True):
        return

    try:
        set_syncing(True)

        from mikrotik.dns_service import MikrotikDNSBlockingService
        service = MikrotikDNSBlockingService()

        if instance.is_active:
            if created or not instance.mikrotik_id:
                # Nouvel ajout
                result = service.add_blocked_domain(instance)
                action = 'ajouté'
            else:
                # Mise à jour
                result = service.update_blocked_domain(instance)
                action = 'mis à jour'

            if result.get('success'):
                logger.info(f"🚫 BlockedSite '{instance.domain}' {action} sur MikroTik DNS")
            else:
                logger.warning(
                    f"⚠️ Échec sync BlockedSite '{instance.domain}': {result.get('error')}"
                )
                log_sync_failure('mikrotik_dns', instance, result.get('error'))
        else:
            # Site désactivé, supprimer de MikroTik
            if instance.mikrotik_id:
                result = service.remove_blocked_domain(instance)
                if result.get('success'):
                    logger.info(f"✅ BlockedSite '{instance.domain}' supprimé de MikroTik DNS")
                else:
                    logger.warning(
                        f"⚠️ Échec suppression BlockedSite '{instance.domain}': {result.get('error')}"
                    )

    except Exception as e:
        logger.error(f"Erreur sync BlockedSite '{instance.domain}': {e}")
        log_sync_failure('mikrotik_dns', instance, e)
    finally:
        set_syncing(False)


@receiver(post_delete, sender=BlockedSite)
def remove_blocked_site_from_mikrotik(sender, instance, **kwargs):
    """
    Supprime un BlockedSite de MikroTik DNS après suppression.
    """
    if is_syncing() or not get_sync_enabled():
        return

    # Pas de MikroTik ID = rien à supprimer
    if not instance.mikrotik_id:
        return

    # Vérifier si MikroTik est activé
    if not getattr(settings, 'MIKROTIK_SYNC_ENABLED', True):
        return

    try:
        set_syncing(True)

        from mikrotik.dns_service import MikrotikDNSBlockingService
        service = MikrotikDNSBlockingService()

        result = service.remove_blocked_domain(instance)

        if result.get('success'):
            logger.info(f"🗑️ BlockedSite '{instance.domain}' supprimé de MikroTik DNS")
        else:
            logger.warning(
                f"⚠️ Échec suppression BlockedSite '{instance.domain}': {result.get('error')}"
            )

    except Exception as e:
        logger.error(f"Erreur suppression BlockedSite '{instance.domain}': {e}")
    finally:
        set_syncing(False)

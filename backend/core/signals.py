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
import logging

from .models import User, Profile, Promotion, ProfileHistory, UserProfileUsage

logger = logging.getLogger(__name__)

# Flag pour éviter les boucles de signals
_syncing = False


def get_sync_enabled() -> bool:
    """Vérifie si la synchronisation automatique est activée."""
    return getattr(settings, 'PROFILE_AUTO_SYNC', True)


def set_syncing(value: bool):
    """Active/désactive le flag de synchronisation."""
    global _syncing
    _syncing = value


def is_syncing() -> bool:
    """Vérifie si une synchronisation est en cours."""
    return _syncing


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
    Synchronise l'utilisateur avec RADIUS et MikroTik après modification.

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

        from radius.services import ProfileRadiusService

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
            ProfileRadiusService.sync_user_to_radius(instance)
            logger.info(f"User '{instance.username}' synced with new profile")

        # Synchroniser avec MikroTik
        if getattr(settings, 'MIKROTIK_SYNC_ENABLED', True):
            try:
                from mikrotik.profile_service import MikrotikProfileSyncService
                mikrotik_service = MikrotikProfileSyncService()

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
    Supprime l'utilisateur de RADIUS et MikroTik lors de la suppression.
    """
    if is_syncing() or not get_sync_enabled():
        return

    try:
        set_syncing(True)

        from radius.models import RadCheck, RadReply, RadUserGroup
        RadCheck.objects.filter(username=instance.username).delete()
        RadReply.objects.filter(username=instance.username).delete()
        RadUserGroup.objects.filter(username=instance.username).delete()
        logger.info(f"User '{instance.username}' removed from RADIUS")

        if getattr(settings, 'MIKROTIK_SYNC_ENABLED', True):
            try:
                from mikrotik.profile_service import MikrotikProfileSyncService
                mikrotik_service = MikrotikProfileSyncService()
                mikrotik_service.delete_hotspot_user(instance.username)
            except Exception as e:
                logger.warning(f"MikroTik delete failed for '{instance.username}': {e}")

    except Exception as e:
        logger.error(f"Error deleting user '{instance.username}' from RADIUS: {e}")
    finally:
        set_syncing(False)


# =============================================================================
# Profile Synchronization to MikroTik
# =============================================================================

@receiver(post_save, sender=Profile)
def sync_profile_to_mikrotik(sender, instance, created, **kwargs):
    """
    Synchronise le profil vers MikroTik après création/modification.
    Met également à jour tous les utilisateurs utilisant ce profil.
    """
    if is_syncing() or not get_sync_enabled():
        return

    if not getattr(settings, 'MIKROTIK_SYNC_ENABLED', True):
        return

    try:
        set_syncing(True)

        from mikrotik.profile_service import MikrotikProfileSyncService
        mikrotik_service = MikrotikProfileSyncService()

        result = mikrotik_service.sync_profile(instance)

        if result.get('success'):
            action = 'created' if created else 'updated'
            logger.info(f"Profile '{instance.name}' {action} in MikroTik")

            # Si modification, mettre à jour les utilisateurs
            if not created:
                sync_users_with_profile_change(instance, mikrotik_service)
        else:
            logger.warning(f"Failed to sync profile '{instance.name}' to MikroTik: {result.get('error')}")

    except Exception as e:
        logger.error(f"Error syncing profile '{instance.name}': {e}")
    finally:
        set_syncing(False)


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
def remove_profile_from_mikrotik(sender, instance, **kwargs):
    """
    Supprime le profil de MikroTik lors de la suppression.
    """
    if is_syncing() or not get_sync_enabled():
        return

    if not getattr(settings, 'MIKROTIK_SYNC_ENABLED', True):
        return

    try:
        set_syncing(True)

        from mikrotik.profile_service import MikrotikProfileSyncService
        mikrotik_service = MikrotikProfileSyncService()

        profile_name = mikrotik_service._get_mikrotik_profile_name(instance)
        result = mikrotik_service.delete_hotspot_profile(profile_name)

        if result.get('success'):
            logger.info(f"Profile '{instance.name}' deleted from MikroTik")

    except Exception as e:
        logger.error(f"Error deleting profile '{instance.name}' from MikroTik: {e}")
    finally:
        set_syncing(False)


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
    Synchronise les utilisateurs de la promotion après modification.
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

        from radius.services import PromotionRadiusService

        if status_changed and not instance.is_active:
            result = PromotionRadiusService.deactivate_promotion(
                instance,
                reason='promotion_disabled'
            )
            logger.info(f"Promotion '{instance.name}' deactivated: {result.get('deactivated', 0)} users")

        elif profile_changed and instance.profile:
            result = PromotionRadiusService.sync_promotion_users(instance)
            logger.info(f"Promotion '{instance.name}' profile changed: {result.get('synced', 0)} users synced")

            if getattr(settings, 'MIKROTIK_SYNC_ENABLED', True):
                try:
                    from mikrotik.profile_service import MikrotikProfileSyncService
                    mikrotik_service = MikrotikProfileSyncService()
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

def sync_all_to_radius_and_mikrotik():
    """
    Utilitaire pour synchroniser tous les profils et utilisateurs.
    À utiliser après configuration initiale ou en cas de désynchronisation.
    """
    from mikrotik.profile_service import FullProfileSyncService

    logger.info("Starting full sync to RADIUS and MikroTik...")

    service = FullProfileSyncService()
    result = service.sync_all()

    logger.info(f"Full sync completed: {result}")

    return result

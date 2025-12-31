"""
Signals for automatic synchronization between Django Users and FreeRADIUS
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import RadCheck, RadReply, RadUserGroup

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=User)
def sync_user_to_radius(sender, instance, created, **kwargs):
    """
    Automatically sync Django user to FreeRADIUS tables on UPDATE only

    Note: User creation is handled by the register endpoint to preserve plain password
    This signal only handles:
    - User deactivation (removes from RADIUS)
    - Role changes (updates group membership)
    - Status changes
    """
    # Skip new user creation - handled by register endpoint
    if created:
        logger.debug("User '%s' created - RADIUS entry handled by register endpoint", instance.username)
        return

    # Handle user deactivation
    if not instance.is_active:
        # If user is deactivated, disable in RADIUS (using statut field instead of deleting)
        # This preserves user configuration and allows re-activation
        updated_count = RadCheck.objects.filter(username=instance.username).update(statut=False)
        if updated_count > 0:
            logger.info("User '%s' deactivated - RADIUS access disabled", instance.username)
        else:
            logger.debug("User '%s' deactivated - no RADIUS entry to disable", instance.username)
        return

    # If user is re-activated, ensure RADIUS entry is enabled
    if instance.is_active and instance.is_radius_activated:
        RadCheck.objects.filter(username=instance.username).update(statut=True)
        logger.info("User '%s' reactivated - RADIUS access enabled", instance.username)

    # Only update role-based settings (not password - it's already hashed)
    # Determine session timeout based on user role
    if instance.role == 'admin':
        session_timeout = 86400  # 24 hours for admins
        groupname = 'admin'
    else:
        session_timeout = 3600  # 1 hour for regular users
        groupname = 'user'

    # Update session timeout in radreply
    RadReply.objects.update_or_create(
        username=instance.username,
        attribute='Session-Timeout',
        defaults={
            'value': str(session_timeout),
            'op': '='
        }
    )

    # Update group membership in radusergroup
    RadUserGroup.objects.update_or_create(
        username=instance.username,
        groupname=groupname,
        defaults={'priority': 0}
    )

    logger.debug("User '%s' settings updated in RADIUS (group: '%s')", instance.username, groupname)


@receiver(post_delete, sender=User)
def remove_user_from_radius(sender, instance, **kwargs):
    """
    Remove user from FreeRADIUS tables when deleted from Django
    """
    RadCheck.objects.filter(username=instance.username).delete()
    RadReply.objects.filter(username=instance.username).delete()
    RadUserGroup.objects.filter(username=instance.username).delete()
    logger.info("User '%s' removed from RADIUS", instance.username)


def sync_all_users_to_radius():
    """
    Utility function to sync all existing Django users to FreeRADIUS
    Run this after setting up FreeRADIUS for the first time
    """
    User = get_user_model()
    users = User.objects.filter(is_active=True)

    logger.info("Starting sync of all users to FreeRADIUS")

    synced_count = 0
    for user in users:
        # Trigger the signal manually
        sync_user_to_radius(User, user, created=False, raw=False, using='default', update_fields=None)
        synced_count += 1

    logger.info("Synced %d users to FreeRADIUS", synced_count)

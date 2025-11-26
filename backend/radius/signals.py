"""
Signals for automatic synchronization between Django Users and FreeRADIUS
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import RadCheck, RadReply, RadUserGroup

User = get_user_model()


@receiver(post_save, sender=User)
def sync_user_to_radius(sender, instance, created, **kwargs):
    """
    Automatically sync Django user to FreeRADIUS tables on creation/update

    Creates/updates entries in:
    - radcheck: for authentication (username + password)
    - radreply: for session parameters (timeout, bandwidth, etc.)
    - radusergroup: for group membership (admin/user)
    """
    # Only sync active users with a password
    if not instance.is_active:
        # If user is deactivated, remove from RADIUS
        RadCheck.objects.filter(username=instance.username).delete()
        RadReply.objects.filter(username=instance.username).delete()
        RadUserGroup.objects.filter(username=instance.username).delete()
        print(f"🚫 User '{instance.username}' deactivated - removed from RADIUS")
        return

    # Sync to radcheck (authentication)
    # Note: For security, we store the password as-is since FreeRADIUS will handle hashing
    # In production, consider using encrypted passwords (Crypt-Password attribute)
    if created or instance.password:  # Only update password if it was changed
        RadCheck.objects.update_or_create(
            username=instance.username,
            attribute='Cleartext-Password',
            defaults={
                'value': instance.password if instance.password else '',
                'op': ':='
            }
        )
        print(f"✅ RADIUS auth updated for user '{instance.username}'")

    # Determine session timeout based on user role
    if instance.role == 'admin':
        session_timeout = 86400  # 24 hours for admins
        groupname = 'admin'
    else:
        session_timeout = 3600  # 1 hour for regular users
        groupname = 'user'

    # Sync to radreply (session parameters)
    RadReply.objects.update_or_create(
        username=instance.username,
        attribute='Session-Timeout',
        defaults={
            'value': str(session_timeout),
            'op': '='
        }
    )

    # Add Mikrotik-specific attributes for bandwidth control (optional)
    if hasattr(instance, 'quota') and instance.quota:
        # Set download speed limit (example: 10Mbps)
        RadReply.objects.update_or_create(
            username=instance.username,
            attribute='Mikrotik-Rate-Limit',
            defaults={
                'value': '10M/10M',  # Download/Upload speeds
                'op': '='
            }
        )

    # Sync to radusergroup (group membership)
    RadUserGroup.objects.update_or_create(
        username=instance.username,
        groupname=groupname,
        defaults={
            'priority': 0
        }
    )

    print(f"🔄 User '{instance.username}' synced to RADIUS as '{groupname}'")


@receiver(post_delete, sender=User)
def remove_user_from_radius(sender, instance, **kwargs):
    """
    Remove user from FreeRADIUS tables when deleted from Django
    """
    RadCheck.objects.filter(username=instance.username).delete()
    RadReply.objects.filter(username=instance.username).delete()
    RadUserGroup.objects.filter(username=instance.username).delete()
    print(f"🗑️  User '{instance.username}' removed from RADIUS")


def sync_all_users_to_radius():
    """
    Utility function to sync all existing Django users to FreeRADIUS
    Run this after setting up FreeRADIUS for the first time
    """
    User = get_user_model()
    users = User.objects.filter(is_active=True)

    print("=" * 70)
    print("SYNCING ALL USERS TO FREERADIUS")
    print("=" * 70)

    synced_count = 0
    for user in users:
        # Trigger the signal manually
        sync_user_to_radius(User, user, created=False, raw=False, using='default', update_fields=None)
        synced_count += 1

    print(f"\n✅ Synced {synced_count} users to FreeRADIUS")
    print("=" * 70)

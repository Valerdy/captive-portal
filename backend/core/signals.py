"""
Signals for automatic role synchronization with Django permissions
and profile change tracking.
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import User, ProfileHistory, UserProfileUsage


@receiver(pre_save, sender=User)
def sync_role_with_permissions(sender, instance, **kwargs):
    """
    Synchronize user role with is_staff and is_superuser flags.

    Priority:
    1. is_staff=True or is_superuser=True → admin role
    2. Otherwise → user role
    """
    # Sync role based on Django permissions
    if instance.is_staff or instance.is_superuser:
        instance.role = 'admin'
    elif not instance.role or instance.role == 'admin':
        # If role is None or was admin but is_staff/is_superuser are now False
        # Downgrade to user role
        instance.role = 'user'


@receiver(post_save, sender=User)
def log_role_assignment(sender, instance, created, **kwargs):
    """Log role assignments for debugging"""
    if created:
        print(f"✅ User '{instance.username}' created with role: {instance.role}")
    else:
        print(f"🔄 User '{instance.username}' role synced to: {instance.role}")


# ============================================================================
# Profile Change Tracking Signals
# ============================================================================

@receiver(pre_save, sender=User)
def track_profile_change(sender, instance, **kwargs):
    """
    Track profile changes before saving User model.
    Stores the old profile ID in instance._old_profile_id for comparison in post_save.
    """
    if instance.pk:  # Only for existing users
        try:
            old_instance = User.objects.get(pk=instance.pk)
            instance._old_profile_id = old_instance.profile_id if old_instance.profile else None
        except User.DoesNotExist:
            instance._old_profile_id = None
    else:
        instance._old_profile_id = None


@receiver(post_save, sender=User)
def create_profile_history(sender, instance, created, **kwargs):
    """
    Create ProfileHistory entry after User is saved if profile changed.
    Also creates/updates UserProfileUsage when profile is assigned.
    """
    # Skip if this is a new user creation without profile
    if created and not instance.profile:
        return

    # Get old profile ID from pre_save signal
    old_profile_id = getattr(instance, '_old_profile_id', None)
    new_profile_id = instance.profile_id if instance.profile else None

    # Check if profile changed
    if old_profile_id != new_profile_id:
        # Determine change type
        if old_profile_id is None and new_profile_id is not None:
            change_type = 'assigned'
        elif old_profile_id is not None and new_profile_id is None:
            change_type = 'removed'
        elif old_profile_id is not None and new_profile_id is not None:
            change_type = 'updated'
        else:
            return  # No change

        # Create history entry
        # Note: changed_by will need to be set via request context in views
        # For now, we create the entry without changed_by
        ProfileHistory.objects.create(
            user=instance,
            old_profile_id=old_profile_id,
            new_profile_id=new_profile_id,
            change_type=change_type,
            reason=f"Profil automatiquement modifié ({change_type})"
        )

        # Handle UserProfileUsage
        if new_profile_id is not None:
            # Create or reset UserProfileUsage when profile is assigned/updated
            usage, usage_created = UserProfileUsage.objects.get_or_create(
                user=instance,
                defaults={
                    'is_active': True
                }
            )

            if not usage_created and change_type == 'updated':
                # Reset usage counters when profile changes
                usage.reset_all()
        elif new_profile_id is None:
            # Deactivate UserProfileUsage when profile is removed
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
    This is a safety net to create UserProfileUsage if it doesn't exist.
    """
    if instance.profile or (instance.promotion and instance.promotion.profile):
        UserProfileUsage.objects.get_or_create(
            user=instance,
            defaults={
                'is_active': True
            }
        )

"""
Signals for automatic role synchronization with Django permissions
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import User


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

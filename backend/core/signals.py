"""
Signals for automatic role synchronization with Django permissions
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import User, Role


@receiver(pre_save, sender=User)
def sync_role_with_permissions(sender, instance, **kwargs):
    """
    Synchronize user role with is_staff and is_superuser flags.

    Priority:
    1. is_staff=True or is_superuser=True → admin role
    2. Otherwise → user role
    """
    # Get or create roles
    admin_role, _ = Role.objects.get_or_create(
        name='admin',
        defaults={'description': 'Administrator with full access'}
    )
    user_role, _ = Role.objects.get_or_create(
        name='user',
        defaults={'description': 'Standard user with basic access'}
    )

    # Sync role based on Django permissions
    if instance.is_staff or instance.is_superuser:
        instance.role = admin_role
    elif instance.role is None or instance.role.name == 'admin':
        # If role is None or was admin but is_staff/is_superuser are now False
        # Downgrade to user role
        instance.role = user_role


@receiver(post_save, sender=User)
def log_role_assignment(sender, instance, created, **kwargs):
    """Log role assignments for debugging"""
    if created:
        print(f"✅ User '{instance.username}' created with role: {instance.role.name}")
    else:
        print(f"🔄 User '{instance.username}' role synced to: {instance.role.name}")

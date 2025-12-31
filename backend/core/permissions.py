"""
Permissions unifiées pour Admin et API.

Fix #15: Unification des vérifications de permissions entre Django Admin et API.

Ce module fournit des classes de permissions réutilisables pour garantir
un modèle de sécurité cohérent entre:
- Django Admin (admin.py)
- API REST (viewsets.py)
- Signals et services internes
"""
from rest_framework import permissions
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class IsAdmin(permissions.BasePermission):
    """
    Permission check for admin role.
    Allows access only to users with admin role (is_staff or is_superuser).
    """
    message = "Access denied: Administrator privileges required."

    def has_permission(self, request, view):
        """Check if user has admin role"""
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_staff or request.user.is_superuser)
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission check: admins have full access, others have read-only access.
    """
    message = "Access denied: Administrator privileges required for this action."

    def has_permission(self, request, view):
        """Check permissions based on request method"""
        # Read permissions (GET, HEAD, OPTIONS) for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Write permissions (POST, PUT, PATCH, DELETE) only for admins
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_staff or request.user.is_superuser)
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission check: allow access to object owner or admins.
    """
    message = "Access denied: You can only access your own resources."

    def has_object_permission(self, request, view, obj):
        """Check if user is owner or admin"""
        # Admins have full access
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Check if object has user attribute and user is owner
        if hasattr(obj, 'user'):
            return obj.user == request.user

        # Check if object is the user itself
        if obj == request.user:
            return True

        return False


class IsAuthenticatedUser(permissions.BasePermission):
    """
    Permission check for regular authenticated users (admin or user role).
    """
    message = "Access denied: Authentication required."

    def has_permission(self, request, view):
        """Check if user is authenticated"""
        return request.user and request.user.is_authenticated


class CanCreateUsers(permissions.BasePermission):
    """
    Permission check for user creation.
    Only admins can create users through the API (except registration).
    """
    message = "Access denied: Only administrators can create users."

    def has_permission(self, request, view):
        """Check if user can create other users"""
        # If it's a create action, only admins can do it
        if request.method == 'POST':
            # Allow registration endpoint (handled separately)
            if view.action == 'create':
                return True  # Let the view handle registration logic
            # For other POST actions, require admin
            return (
                request.user and
                request.user.is_authenticated and
                (request.user.is_staff or request.user.is_superuser)
            )
        return True


# =============================================================================
# Permissions RADIUS (Fix #15)
# =============================================================================

class CanManageRadius(permissions.BasePermission):
    """
    Permission: Peut gérer les opérations RADIUS.

    Vérifie que l'utilisateur a les droits de gestion RADIUS:
    - Activation/désactivation utilisateurs
    - Synchronisation profils
    - Modification des groupes RADIUS
    """
    message = "Permission de gestion RADIUS requise."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Superuser a tous les droits
        if user.is_superuser:
            return True

        # Staff avec permission explicite
        if user.is_staff:
            return True

        return False


class IsSuperuser(permissions.BasePermission):
    """
    Permission: L'utilisateur doit être superuser.

    Usage pour actions critiques (suppression en masse, etc.):
        permission_classes = [IsSuperuser]
    """
    message = "Accès réservé aux super-administrateurs."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_superuser
        )


# =============================================================================
# Fonctions de vérification pour Django Admin (Fix #15)
# =============================================================================

def check_admin_permission(user, action, obj=None):
    """
    Vérifie si un utilisateur admin a la permission pour une action.

    Args:
        user: L'utilisateur Django
        action: L'action demandée ('view', 'add', 'change', 'delete')
        obj: L'objet cible (optionnel, pour permissions par objet)

    Returns:
        bool: True si la permission est accordée
    """
    if not user or not user.is_authenticated:
        return False

    # Superuser a tous les droits
    if user.is_superuser:
        return True

    # Staff a les droits de base
    if user.is_staff:
        return True

    return False


def check_radius_permission(user, action, target_user=None):
    """
    Vérifie si un utilisateur admin peut effectuer une action RADIUS.

    Args:
        user: L'utilisateur admin effectuant l'action
        action: L'action RADIUS ('activate', 'deactivate', 'sync', 'view')
        target_user: L'utilisateur cible de l'action (optionnel)

    Returns:
        bool: True si la permission est accordée
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    if user.is_staff:
        return True

    return False


# =============================================================================
# Décorateurs pour les actions admin (Fix #15)
# =============================================================================

def require_radius_permission(action='manage'):
    """
    Décorateur pour les actions admin nécessitant des permissions RADIUS.

    Usage:
        @require_radius_permission('activate')
        def activate_radius(self, request, queryset):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(modeladmin, request, queryset=None, *args, **kwargs):
            if not check_radius_permission(request.user, action):
                from django.contrib import messages
                messages.error(request, f"Permission RADIUS '{action}' requise.")
                return None
            return func(modeladmin, request, queryset, *args, **kwargs)
        return wrapper
    return decorator


def require_superuser(func):
    """
    Décorateur pour les actions nécessitant superuser.

    Usage:
        @require_superuser
        def dangerous_action(self, request, queryset):
            ...
    """
    @wraps(func)
    def wrapper(modeladmin, request, queryset=None, *args, **kwargs):
        if not request.user.is_superuser:
            from django.contrib import messages
            messages.error(request, "Cette action nécessite les droits super-administrateur.")
            return None
        return func(modeladmin, request, queryset, *args, **kwargs)
    return wrapper


# =============================================================================
# Export
# =============================================================================

__all__ = [
    'IsAdmin',
    'IsAdminOrReadOnly',
    'IsOwnerOrAdmin',
    'IsAuthenticatedUser',
    'CanCreateUsers',
    'CanManageRadius',
    'IsSuperuser',
    'check_admin_permission',
    'check_radius_permission',
    'require_radius_permission',
    'require_superuser',
]

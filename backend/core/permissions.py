"""
Custom permissions for role-based access control
"""
from rest_framework import permissions


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

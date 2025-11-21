"""
Custom decorators for role-based access control
"""
from functools import wraps
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from rest_framework import status


def role_required(*required_roles):
    """
    Decorator to check if user has one of the required roles.

    Usage:
        @role_required('admin')
        def my_view(request):
            ...

        @role_required('admin', 'user')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Get user's role
            user = request.user
            user_role = user.get_role_name()

            # Check if user has one of the required roles
            if user_role not in required_roles:
                return JsonResponse(
                    {
                        'error': 'Access denied',
                        'detail': f'This resource requires one of the following roles: {", ".join(required_roles)}',
                        'your_role': user_role
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required(view_func):
    """
    Decorator to check if user is an admin.

    Usage:
        @admin_required
        def my_view(request):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user

        # Check if user is admin
        if not (user.is_staff or user.is_superuser):
            return JsonResponse(
                {
                    'error': 'Access denied',
                    'detail': 'Administrator privileges required',
                    'your_role': user.get_role_name()
                },
                status=status.HTTP_403_FORBIDDEN
            )

        return view_func(request, *args, **kwargs)
    return wrapper


def user_required(view_func):
    """
    Decorator to check if user is authenticated (any role).

    Usage:
        @user_required
        def my_view(request):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return wrapper


def owner_or_admin_required(get_object_func):
    """
    Decorator to check if user is the owner of the object or an admin.

    Usage:
        def get_device(device_id):
            return Device.objects.get(id=device_id)

        @owner_or_admin_required(get_device)
        def my_view(request, device_id):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user = request.user

            # Admins have full access
            if user.is_staff or user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Get the object
            try:
                obj = get_object_func(*args, **kwargs)
            except Exception as e:
                return JsonResponse(
                    {'error': 'Object not found', 'detail': str(e)},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check ownership
            if hasattr(obj, 'user') and obj.user == user:
                return view_func(request, *args, **kwargs)
            elif obj == user:
                return view_func(request, *args, **kwargs)
            else:
                return JsonResponse(
                    {
                        'error': 'Access denied',
                        'detail': 'You can only access your own resources'
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

        return wrapper
    return decorator

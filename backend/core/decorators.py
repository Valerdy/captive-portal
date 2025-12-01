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


# =============================================================================
# Rate Limiting Decorators
# =============================================================================

def get_client_ip(request):
    """
    Get the client IP address from the request.
    Handles proxy headers (X-Forwarded-For).
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def rate_limit(key_prefix='rl', rate='5/m', method='ALL', block_duration=60):
    """
    Custom rate limiting decorator.

    Args:
        key_prefix (str): Prefix for cache key
        rate (str): Rate limit in format 'count/period' where period is:
                    s=second, m=minute, h=hour, d=day
                    Examples: '5/m' = 5 per minute, '100/h' = 100 per hour
        method (str): HTTP method to limit ('GET', 'POST', 'ALL')
        block_duration (int): Duration in seconds to block after exceeding limit

    Returns:
        function: Decorated view function

    Example:
        @rate_limit(key_prefix='login', rate='5/m', method='POST')
        def login_view(request):
            ...
    """
    from django.core.cache import cache
    from django.conf import settings
    import hashlib
    import time

    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Skip rate limiting in DEBUG mode if configured
            if getattr(settings, 'DISABLE_RATE_LIMIT_IN_DEBUG', False) and settings.DEBUG:
                return view_func(request, *args, **kwargs)

            # Check if method matches
            if method != 'ALL' and request.method != method:
                return view_func(request, *args, **kwargs)

            # Parse rate
            try:
                count, period = rate.split('/')
                count = int(count)
                period_map = {
                    's': 1,
                    'm': 60,
                    'h': 3600,
                    'd': 86400
                }
                period_seconds = period_map.get(period, 60)
            except (ValueError, KeyError):
                # Default to 5 per minute if parsing fails
                count = 5
                period_seconds = 60

            # Get client identifier (IP address)
            client_ip = get_client_ip(request)
            client_id = hashlib.md5(client_ip.encode()).hexdigest()

            # Create cache keys
            cache_key = f'{key_prefix}:{client_id}'
            block_key = f'{key_prefix}:block:{client_id}'

            # Check if client is blocked
            if cache.get(block_key):
                remaining_block_time = cache.ttl(block_key) or block_duration
                return JsonResponse({
                    'error': 'Rate limit exceeded',
                    'detail': f'Too many requests. Please try again in {remaining_block_time} seconds.',
                    'retry_after': remaining_block_time
                }, status=429)

            # Get current request count
            current_count = cache.get(cache_key, 0)

            if current_count >= count:
                # Block the client
                cache.set(block_key, True, block_duration)
                return JsonResponse({
                    'error': 'Rate limit exceeded',
                    'detail': f'Too many requests. You have been blocked for {block_duration} seconds.',
                    'retry_after': block_duration
                }, status=429)

            # Increment counter
            if current_count == 0:
                cache.set(cache_key, 1, period_seconds)
            else:
                cache.incr(cache_key)

            # Add rate limit headers to response
            response = view_func(request, *args, **kwargs)
            if hasattr(response, '__setitem__'):
                response['X-RateLimit-Limit'] = str(count)
                response['X-RateLimit-Remaining'] = str(max(0, count - current_count - 1))
                response['X-RateLimit-Reset'] = str(int(time.time()) + period_seconds)

            return response

        return wrapped_view
    return decorator

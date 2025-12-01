"""
Custom middleware for JWT cookie authentication
"""
from django.utils.functional import SimpleLazyObject
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


def get_user_from_cookie(request):
    """
    Get user from JWT cookie if available.

    Args:
        request: Django request object

    Returns:
        User object or AnonymousUser
    """
    # Check if token is in cookie
    access_token = request.COOKIES.get('access_token')

    if not access_token:
        from django.contrib.auth.models import AnonymousUser
        return AnonymousUser()

    try:
        # Validate token using JWT authentication
        jwt_auth = JWTAuthentication()
        validated_token = jwt_auth.get_validated_token(access_token)
        user = jwt_auth.get_user(validated_token)
        return user
    except (InvalidToken, TokenError):
        from django.contrib.auth.models import AnonymousUser
        return AnonymousUser()


class JWTCookieMiddleware:
    """
    Middleware to handle JWT authentication from cookies.

    This middleware checks for JWT tokens in cookies and authenticates
    the user if a valid token is found. This allows cookie-based authentication
    instead of requiring tokens in the Authorization header.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # If there's no Authorization header, try to get token from cookie
        if not request.META.get('HTTP_AUTHORIZATION'):
            access_token = request.COOKIES.get('access_token')

            if access_token:
                # Add token to request headers for DRF authentication
                request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'

        response = self.get_response(request)
        return response


class JWTCookieAuthenticationMiddleware:
    """
    Alternative middleware that sets request.user from cookie.

    This is a more direct approach that bypasses the need to modify
    the Authorization header.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only process if user is not already authenticated
        if not hasattr(request, 'user') or request.user.is_anonymous:
            request.user = SimpleLazyObject(lambda: get_user_from_cookie(request))

        response = self.get_response(request)
        return response

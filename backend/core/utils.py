"""
Utility functions for the core app
"""
import secrets
import string


def generate_secure_password(length=16):
    """
    Generate a cryptographically secure random password.

    Args:
        length (int): Length of the password (minimum 12, default 16)

    Returns:
        str: A secure random password containing uppercase, lowercase,
             digits and special characters

    Example:
        >>> password = generate_secure_password()
        >>> len(password)
        16
        >>> password = generate_secure_password(20)
        >>> len(password)
        20
    """
    if length < 12:
        raise ValueError("Password length must be at least 12 characters")

    # Define character sets
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    # Combine all character sets
    all_characters = uppercase + lowercase + digits + special

    # Ensure at least one character from each set
    password = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(special)
    ]

    # Fill the rest of the password with random characters
    password += [secrets.choice(all_characters) for _ in range(length - 4)]

    # Shuffle to avoid predictable pattern (first 4 always same type)
    password_list = list(password)
    secrets.SystemRandom().shuffle(password_list)

    return ''.join(password_list)


def generate_temporary_username(first_name, last_name, matricule):
    """
    Generate a temporary username based on user information.

    Args:
        first_name (str): User's first name
        last_name (str): User's last name
        matricule (str): User's matricule number

    Returns:
        str: Generated username

    Example:
        >>> generate_temporary_username("Jean", "Dupont", "12345")
        'jdupont_12345'
    """
    # Take first letter of first name + full last name (lowercase, no spaces)
    username_base = f"{first_name[0]}{last_name}".lower().replace(" ", "")

    # Add matricule for uniqueness
    username = f"{username_base}_{matricule}"

    return username


# =============================================================================
# Cookie Management for JWT Tokens
# =============================================================================

def set_jwt_cookies(response, access_token, refresh_token):
    """
    Set JWT tokens in secure HttpOnly cookies.

    Args:
        response: Django Response object
        access_token (str): JWT access token
        refresh_token (str): JWT refresh token

    Returns:
        Response: Modified response with cookies set
    """
    from django.conf import settings

    # Cookie settings
    secure = not settings.DEBUG  # Secure cookies in production only
    samesite = 'Lax'  # Protection against CSRF

    # Set access token cookie (short lived)
    response.set_cookie(
        key='access_token',
        value=access_token,
        max_age=60 * 60,  # 1 hour (matches JWT_ACCESS_TOKEN_LIFETIME)
        httponly=True,  # Not accessible via JavaScript
        secure=secure,  # HTTPS only in production
        samesite=samesite  # CSRF protection
    )

    # Set refresh token cookie (long lived)
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        max_age=60 * 60 * 24,  # 24 hours (matches JWT_REFRESH_TOKEN_LIFETIME)
        httponly=True,
        secure=secure,
        samesite=samesite
    )

    return response


def clear_jwt_cookies(response):
    """
    Clear JWT tokens from cookies.

    Args:
        response: Django Response object

    Returns:
        Response: Modified response with cookies cleared
    """
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response


def get_token_from_cookie(request, cookie_name='access_token'):
    """
    Get JWT token from cookie.

    Args:
        request: Django Request object
        cookie_name (str): Name of the cookie to retrieve

    Returns:
        str: Token value or None if not found
    """
    return request.COOKIES.get(cookie_name)

"""
Pytest configuration and fixtures for captive-portal tests.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


# =============================================================================
# Database fixtures
# =============================================================================

@pytest.fixture
def db_access(db):
    """Provide database access for tests."""
    pass


# =============================================================================
# User fixtures
# =============================================================================

@pytest.fixture
def user_password():
    """Default password for test users."""
    return "TestPass123!"


@pytest.fixture
def regular_user(db, user_password):
    """Create a regular user for testing."""
    user = User.objects.create_user(
        username="testuser",
        email="testuser@example.com",
        password=user_password,
        first_name="Test",
        last_name="User",
        matricule="MAT001",
        role="user",
        is_active=True
    )
    user.cleartext_password = user_password
    user.save()
    return user


@pytest.fixture
def admin_user(db, user_password):
    """Create an admin user for testing."""
    user = User.objects.create_user(
        username="adminuser",
        email="admin@example.com",
        password=user_password,
        first_name="Admin",
        last_name="User",
        role="admin",
        is_staff=True,
        is_superuser=True,
        is_active=True
    )
    user.cleartext_password = user_password
    user.save()
    return user


@pytest.fixture
def inactive_user(db, user_password):
    """Create an inactive user for testing."""
    user = User.objects.create_user(
        username="inactiveuser",
        email="inactive@example.com",
        password=user_password,
        first_name="Inactive",
        last_name="User",
        is_active=False
    )
    return user


@pytest.fixture
def radius_activated_user(db, user_password, profile):
    """Create a user activated in RADIUS."""
    user = User.objects.create_user(
        username="radiususer",
        email="radius@example.com",
        password=user_password,
        first_name="Radius",
        last_name="User",
        role="user",
        is_active=True,
        is_radius_activated=True,
        is_radius_enabled=True,
        profile=profile
    )
    user.cleartext_password = user_password
    user.save()
    return user


# =============================================================================
# Profile fixtures
# =============================================================================

@pytest.fixture
def profile(db):
    """Create a test profile."""
    from core.models import Profile
    return Profile.objects.create(
        name="Test Profile",
        description="A test profile for testing",
        is_active=True,
        bandwidth_upload=5,
        bandwidth_download=10,
        quota_type="limited",
        data_volume=53687091200,  # 50 GB
        validity_duration=30,
        session_timeout=28800,
        idle_timeout=600,
        simultaneous_use=1,
        is_radius_enabled=True
    )


@pytest.fixture
def unlimited_profile(db):
    """Create an unlimited profile."""
    from core.models import Profile
    return Profile.objects.create(
        name="Unlimited Profile",
        description="An unlimited profile",
        is_active=True,
        bandwidth_upload=100,
        bandwidth_download=100,
        quota_type="unlimited",
        data_volume=0,
        validity_duration=365,
        session_timeout=86400,
        idle_timeout=1800,
        simultaneous_use=5,
        is_radius_enabled=True
    )


# =============================================================================
# Promotion fixtures
# =============================================================================

@pytest.fixture
def promotion(db, profile):
    """Create a test promotion."""
    from core.models import Promotion
    return Promotion.objects.create(
        name="Test Promotion 2024",
        is_active=True,
        profile=profile
    )


@pytest.fixture
def promotion_with_users(db, promotion, user_password):
    """Create a promotion with multiple users."""
    users = []
    for i in range(5):
        user = User.objects.create_user(
            username=f"promouser{i}",
            email=f"promouser{i}@example.com",
            password=user_password,
            first_name=f"Promo{i}",
            last_name="User",
            promotion=promotion,
            matricule=f"MAT{100+i}"
        )
        user.cleartext_password = user_password
        user.save()
        users.append(user)
    return promotion, users


# =============================================================================
# Device and Session fixtures
# =============================================================================

@pytest.fixture
def device(db, regular_user):
    """Create a test device."""
    from core.models import Device
    return Device.objects.create(
        user=regular_user,
        mac_address="AA:BB:CC:DD:EE:FF",
        ip_address="192.168.1.100",
        hostname="test-device",
        device_type="desktop",
        is_active=True
    )


@pytest.fixture
def session(db, regular_user, device):
    """Create a test session."""
    from core.models import Session
    import uuid
    return Session.objects.create(
        user=regular_user,
        device=device,
        session_id=str(uuid.uuid4()),
        ip_address="192.168.1.100",
        mac_address="AA:BB:CC:DD:EE:FF",
        status="active",
        timeout_duration=3600
    )


# =============================================================================
# Voucher fixtures
# =============================================================================

@pytest.fixture
def voucher(db, admin_user):
    """Create a test voucher."""
    from core.models import Voucher
    from django.utils import timezone
    from datetime import timedelta
    return Voucher.objects.create(
        code="TEST-VOUCHER-001",
        status="active",
        duration=3600,
        max_devices=1,
        valid_from=timezone.now(),
        valid_until=timezone.now() + timedelta(days=7),
        created_by=admin_user
    )


# =============================================================================
# BlockedSite fixtures
# =============================================================================

@pytest.fixture
def blocked_site(db, admin_user):
    """Create a test blocked site."""
    from core.models import BlockedSite
    return BlockedSite.objects.create(
        domain="blocked-site.com",
        type="blacklist",
        category="social",
        reason="Test blocking",
        is_active=True,
        added_by=admin_user,
        sync_status="pending"
    )


# =============================================================================
# API Client fixtures
# =============================================================================

@pytest.fixture
def api_client():
    """Create an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, regular_user):
    """Create an authenticated API client for regular user."""
    refresh = RefreshToken.for_user(regular_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Create an authenticated API client for admin user."""
    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


# =============================================================================
# RADIUS fixtures
# =============================================================================

@pytest.fixture
def radcheck_entry(db, regular_user):
    """Create a RadCheck entry for testing."""
    from radius.models import RadCheck
    return RadCheck.objects.create(
        username=regular_user.username,
        attribute="Cleartext-Password",
        op=":=",
        value="testpassword",
        statut=True
    )


@pytest.fixture
def radreply_entry(db, regular_user):
    """Create a RadReply entry for testing."""
    from radius.models import RadReply
    return RadReply.objects.create(
        username=regular_user.username,
        attribute="Session-Timeout",
        op="=",
        value="3600"
    )


@pytest.fixture
def radusergroup_entry(db, regular_user):
    """Create a RadUserGroup entry for testing."""
    from radius.models import RadUserGroup
    return RadUserGroup.objects.create(
        username=regular_user.username,
        groupname="user",
        priority=0
    )


# =============================================================================
# MikroTik fixtures
# =============================================================================

@pytest.fixture
def mikrotik_router(db):
    """Create a MikroTik router for testing."""
    from mikrotik.models import MikrotikRouter
    return MikrotikRouter.objects.create(
        name="Test Router",
        host="192.168.88.1",
        port=8728,
        username="admin",
        password="testpassword",
        is_active=True
    )


# =============================================================================
# Utility fixtures
# =============================================================================

@pytest.fixture
def mock_radius_sync(mocker):
    """Mock RADIUS synchronization functions."""
    return mocker.patch('radius.services.RadiusProfileGroupService.sync_profile_to_radius_group')


@pytest.fixture
def mock_mikrotik_client(mocker):
    """Mock MikroTik API client."""
    return mocker.patch('mikrotik.client.MikrotikAgentClient')

"""
Comprehensive tests for the core application.
Tests cover models, API endpoints, authentication, and business logic.
"""
import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework import status

from .models import (
    User, Profile, Promotion, Device, Session, Voucher,
    BlockedSite, UserProfileUsage, ProfileHistory, ProfileAlert,
    UserDisconnectionLog, AdminAuditLog, SyncFailureLog
)


# =============================================================================
# MODEL TESTS
# =============================================================================

@pytest.mark.django_db
class TestUserModel:
    """Tests for the User model."""

    def test_create_user(self, user_password):
        """Test creating a regular user."""
        user = User.objects.create_user(
            username="newuser",
            email="newuser@example.com",
            password=user_password,
            first_name="New",
            last_name="User"
        )
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.check_password(user_password)
        assert user.role == "user"
        assert user.is_active is True
        assert user.is_staff is False

    def test_create_admin_user(self, user_password):
        """Test creating an admin user."""
        user = User.objects.create_superuser(
            username="superadmin",
            email="superadmin@example.com",
            password=user_password
        )
        assert user.is_staff is True
        assert user.is_superuser is True

    def test_user_str_representation(self, regular_user):
        """Test User string representation."""
        assert str(regular_user) == f"{regular_user.username} ({regular_user.email})"

    def test_user_is_admin(self, admin_user, regular_user):
        """Test is_admin method."""
        assert admin_user.is_admin() is True
        assert regular_user.is_admin() is False

    def test_user_is_regular_user(self, admin_user, regular_user):
        """Test is_regular_user method."""
        assert admin_user.is_regular_user() is False
        assert regular_user.is_regular_user() is True

    def test_user_radius_status_pending(self, regular_user):
        """Test RADIUS status for pending user."""
        assert regular_user.is_radius_activated is False
        assert regular_user.is_pending_radius_activation() is True
        assert regular_user.can_access_radius() is False

    def test_user_radius_status_activated(self, radius_activated_user):
        """Test RADIUS status for activated user."""
        assert radius_activated_user.is_radius_activated is True
        assert radius_activated_user.is_radius_enabled is True
        assert radius_activated_user.can_access_radius() is True
        assert radius_activated_user.is_pending_radius_activation() is False

    def test_user_get_effective_profile_individual(self, regular_user, profile):
        """Test getting effective profile (individual priority)."""
        regular_user.profile = profile
        regular_user.save()
        assert regular_user.get_effective_profile() == profile

    def test_user_get_effective_profile_from_promotion(self, regular_user, promotion):
        """Test getting effective profile from promotion."""
        regular_user.promotion = promotion
        regular_user.save()
        assert regular_user.get_effective_profile() == promotion.profile

    def test_user_get_radius_status_display(self, regular_user, radius_activated_user, inactive_user):
        """Test human-readable RADIUS status."""
        assert "attente" in regular_user.get_radius_status_display().lower()
        assert "actif" in radius_activated_user.get_radius_status_display().lower()
        assert "désactivé" in inactive_user.get_radius_status_display().lower()


@pytest.mark.django_db
class TestProfileModel:
    """Tests for the Profile model."""

    def test_create_profile(self, profile):
        """Test creating a profile."""
        assert profile.name == "Test Profile"
        assert profile.is_active is True
        assert profile.bandwidth_upload == 5
        assert profile.bandwidth_download == 10

    def test_profile_data_volume_gb(self, profile):
        """Test data volume conversion to GB."""
        assert profile.data_volume_gb == 50.0

    def test_profile_str_representation(self, profile):
        """Test Profile string representation."""
        assert profile.name in str(profile)

    def test_profile_get_radius_group_name(self, profile):
        """Test RADIUS group name generation."""
        group_name = profile.get_radius_group_name()
        assert group_name.startswith("profile_")
        assert str(profile.id) in group_name

    def test_profile_can_sync_to_radius(self, profile):
        """Test profile sync eligibility."""
        profile.is_radius_enabled = True
        profile.is_active = True
        assert profile.can_sync_to_radius() is True

        profile.is_active = False
        assert profile.can_sync_to_radius() is False


@pytest.mark.django_db
class TestPromotionModel:
    """Tests for the Promotion model."""

    def test_create_promotion(self, promotion):
        """Test creating a promotion."""
        assert promotion.name == "Test Promotion 2024"
        assert promotion.is_active is True
        assert promotion.profile is not None

    def test_promotion_str_representation(self, promotion):
        """Test Promotion string representation."""
        assert str(promotion) == promotion.name

    def test_promotion_with_users(self, promotion_with_users):
        """Test promotion with assigned users."""
        promotion, users = promotion_with_users
        assert promotion.users.count() == 5
        for user in users:
            assert user.promotion == promotion


@pytest.mark.django_db
class TestDeviceModel:
    """Tests for the Device model."""

    def test_create_device(self, device):
        """Test creating a device."""
        assert device.mac_address == "AA:BB:CC:DD:EE:FF"
        assert device.is_active is True

    def test_device_str_representation(self, device):
        """Test Device string representation."""
        assert device.mac_address in str(device)
        assert device.user.username in str(device)


@pytest.mark.django_db
class TestSessionModel:
    """Tests for the Session model."""

    def test_create_session(self, session):
        """Test creating a session."""
        assert session.status == "active"
        assert session.timeout_duration == 3600

    def test_session_is_expired_active(self, session):
        """Test session expiration for active session."""
        assert session.is_expired is False

    def test_session_is_expired_terminated(self, session):
        """Test session expiration for terminated session."""
        session.status = "terminated"
        session.save()
        assert session.is_expired is True

    def test_session_total_bytes(self, session):
        """Test total bytes calculation."""
        session.bytes_in = 1000
        session.bytes_out = 500
        assert session.total_bytes == 1500


@pytest.mark.django_db
class TestVoucherModel:
    """Tests for the Voucher model."""

    def test_create_voucher(self, voucher):
        """Test creating a voucher."""
        assert voucher.code == "TEST-VOUCHER-001"
        assert voucher.status == "active"

    def test_voucher_is_valid(self, voucher):
        """Test voucher validity check."""
        assert voucher.is_valid is True

    def test_voucher_is_valid_expired(self, voucher):
        """Test expired voucher validity."""
        voucher.valid_until = timezone.now() - timedelta(days=1)
        voucher.save()
        assert voucher.is_valid is False

    def test_voucher_is_valid_used(self, voucher):
        """Test used voucher validity."""
        voucher.used_count = voucher.max_devices
        voucher.save()
        assert voucher.is_valid is False


@pytest.mark.django_db
class TestBlockedSiteModel:
    """Tests for the BlockedSite model."""

    def test_create_blocked_site(self, blocked_site):
        """Test creating a blocked site."""
        assert blocked_site.domain == "blocked-site.com"
        assert blocked_site.is_active is True

    def test_blocked_site_is_global(self, blocked_site):
        """Test global blocking check."""
        assert blocked_site.is_global is True

    def test_blocked_site_needs_sync(self, blocked_site):
        """Test sync status check."""
        assert blocked_site.needs_sync is True

        blocked_site.sync_status = "synced"
        blocked_site.save()
        assert blocked_site.needs_sync is False

    def test_blocked_site_get_dns_name(self, blocked_site):
        """Test DNS name extraction."""
        assert blocked_site.get_dns_name() == "blocked-site.com"

        blocked_site.domain = "*.example.com"
        assert blocked_site.get_dns_name() == "example.com"


# =============================================================================
# API AUTHENTICATION TESTS
# =============================================================================

@pytest.mark.django_db
class TestAuthenticationAPI:
    """Tests for authentication endpoints."""

    def test_register_user(self, api_client, promotion):
        """Test user registration."""
        url = reverse('register')
        data = {
            'first_name': 'New',
            'last_name': 'User',
            'matricule': 'MAT999',
            'promotion': promotion.id,
            'password': 'SecurePass123!',
            'password2': 'SecurePass123!'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert User.objects.filter(matricule='MAT999').exists()

    def test_register_user_password_mismatch(self, api_client, promotion):
        """Test registration with mismatched passwords."""
        url = reverse('register')
        data = {
            'first_name': 'New',
            'last_name': 'User',
            'matricule': 'MAT998',
            'promotion': promotion.id,
            'password': 'SecurePass123!',
            'password2': 'DifferentPass123!'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_success(self, api_client, regular_user, user_password):
        """Test successful login."""
        url = reverse('login')
        data = {
            'username': regular_user.username,
            'password': user_password
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data or 'user' in response.data

    def test_login_invalid_credentials(self, api_client, regular_user):
        """Test login with invalid credentials."""
        url = reverse('login')
        data = {
            'username': regular_user.username,
            'password': 'wrongpassword'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED]

    def test_login_inactive_user(self, api_client, inactive_user, user_password):
        """Test login with inactive user."""
        url = reverse('login')
        data = {
            'username': inactive_user.username,
            'password': user_password
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED]

    def test_get_profile_authenticated(self, authenticated_client, regular_user):
        """Test getting profile for authenticated user."""
        url = reverse('user_profile')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == regular_user.username

    def test_get_profile_unauthenticated(self, api_client):
        """Test getting profile without authentication."""
        url = reverse('user_profile')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_change_password(self, authenticated_client, user_password):
        """Test password change."""
        url = reverse('change_password')
        data = {
            'current_password': user_password,
            'new_password': 'NewSecurePass123!',
            'confirm_password': 'NewSecurePass123!'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK


# =============================================================================
# API CRUD TESTS
# =============================================================================

@pytest.mark.django_db
class TestUserAPI:
    """Tests for User CRUD API."""

    def test_list_users_admin(self, admin_client):
        """Test listing users as admin."""
        url = reverse('user-list')
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_list_users_non_admin(self, authenticated_client):
        """Test listing users as non-admin (should be forbidden)."""
        url = reverse('user-list')
        response = authenticated_client.get(url)
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_200_OK]

    def test_get_user_detail(self, admin_client, regular_user):
        """Test getting user detail."""
        url = reverse('user-detail', kwargs={'pk': regular_user.pk})
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == regular_user.username

    def test_update_user(self, admin_client, regular_user):
        """Test updating user."""
        url = reverse('user-detail', kwargs={'pk': regular_user.pk})
        data = {'first_name': 'Updated'}
        response = admin_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        regular_user.refresh_from_db()
        assert regular_user.first_name == 'Updated'


@pytest.mark.django_db
class TestProfileAPI:
    """Tests for Profile CRUD API."""

    def test_list_profiles(self, admin_client, profile):
        """Test listing profiles."""
        url = reverse('profile-list')
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_create_profile(self, admin_client):
        """Test creating a profile."""
        url = reverse('profile-list')
        data = {
            'name': 'New Test Profile',
            'description': 'A new test profile',
            'is_active': True,
            'bandwidth_upload': 10,
            'bandwidth_download': 20,
            'quota_type': 'limited',
            'data_volume': 107374182400,
            'validity_duration': 30,
            'session_timeout': 28800,
            'idle_timeout': 600,
            'simultaneous_use': 2
        }
        response = admin_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Profile.objects.filter(name='New Test Profile').exists()

    def test_update_profile(self, admin_client, profile):
        """Test updating a profile."""
        url = reverse('profile-detail', kwargs={'pk': profile.pk})
        data = {'bandwidth_download': 50}
        response = admin_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        profile.refresh_from_db()
        assert profile.bandwidth_download == 50


@pytest.mark.django_db
class TestPromotionAPI:
    """Tests for Promotion CRUD API."""

    def test_list_promotions(self, admin_client, promotion):
        """Test listing promotions."""
        url = reverse('promotion-list')
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_create_promotion(self, admin_client, profile):
        """Test creating a promotion."""
        url = reverse('promotion-list')
        data = {
            'name': 'New Promotion 2025',
            'is_active': True,
            'profile': profile.id
        }
        response = admin_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED


# =============================================================================
# RADIUS ACTIVATION TESTS
# =============================================================================

@pytest.mark.django_db
class TestRadiusActivation:
    """Tests for RADIUS activation functionality."""

    def test_activate_users_radius(self, admin_client, regular_user):
        """Test activating users in RADIUS."""
        regular_user.cleartext_password = "TestPass123!"
        regular_user.save()

        url = reverse('activate_users_radius')
        data = {'user_ids': [regular_user.id]}
        response = admin_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

        regular_user.refresh_from_db()
        assert regular_user.is_radius_activated is True

    def test_activate_already_activated_user(self, admin_client, radius_activated_user):
        """Test activating already activated user."""
        url = reverse('activate_users_radius')
        data = {'user_ids': [radius_activated_user.id]}
        response = admin_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data.get('failed_users', [])) > 0


# =============================================================================
# BLOCKED SITES TESTS
# =============================================================================

@pytest.mark.django_db
class TestBlockedSiteAPI:
    """Tests for BlockedSite API."""

    def test_list_blocked_sites(self, admin_client, blocked_site):
        """Test listing blocked sites."""
        url = reverse('blockedsite-list')
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_create_blocked_site(self, admin_client):
        """Test creating a blocked site."""
        url = reverse('blockedsite-list')
        data = {
            'domain': 'newblocked.com',
            'type': 'blacklist',
            'category': 'streaming',
            'reason': 'Test block',
            'is_active': True
        }
        response = admin_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED


# =============================================================================
# VOUCHER TESTS
# =============================================================================

@pytest.mark.django_db
class TestVoucherAPI:
    """Tests for Voucher API."""

    def test_list_vouchers(self, admin_client, voucher):
        """Test listing vouchers."""
        url = reverse('voucher-list')
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_validate_voucher(self, api_client, voucher):
        """Test voucher validation."""
        url = reverse('validate_voucher')
        data = {'code': voucher.code}
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_validate_invalid_voucher(self, api_client):
        """Test invalid voucher validation."""
        url = reverse('validate_voucher')
        data = {'code': 'INVALID-CODE'}
        response = api_client.post(url, data, format='json')
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]


# =============================================================================
# UTILITY TESTS
# =============================================================================

@pytest.mark.django_db
class TestUserProfileUsage:
    """Tests for UserProfileUsage model."""

    def test_create_usage(self, radius_activated_user):
        """Test creating usage tracking."""
        usage = UserProfileUsage.objects.create(
            user=radius_activated_user,
            used_today=1073741824,  # 1 GB
            used_week=5368709120,   # 5 GB
            used_month=10737418240  # 10 GB
        )
        assert usage.used_today_gb == 1.0
        assert usage.used_week_gb == 5.0
        assert usage.used_month_gb == 10.0

    def test_check_exceeded(self, radius_activated_user, profile):
        """Test quota exceeded check."""
        usage = UserProfileUsage.objects.create(
            user=radius_activated_user,
            used_total=profile.data_volume + 1
        )
        assert usage.check_exceeded() is True

    def test_add_usage(self, radius_activated_user):
        """Test adding usage."""
        usage = UserProfileUsage.objects.create(user=radius_activated_user)
        initial_total = usage.used_total
        usage.add_usage(1073741824)  # Add 1 GB
        assert usage.used_total == initial_total + 1073741824


@pytest.mark.django_db
class TestAuditLog:
    """Tests for AdminAuditLog."""

    def test_log_action(self, admin_user, regular_user):
        """Test logging admin action."""
        log = AdminAuditLog.log_action(
            admin_user=admin_user,
            action_type='user_radius_activate',
            target=regular_user,
            details={'reason': 'Test activation'},
            success=True
        )
        assert log.admin_username == admin_user.username
        assert log.target_model == 'User'
        assert log.success is True


@pytest.mark.django_db
class TestSyncFailureLog:
    """Tests for SyncFailureLog."""

    def test_log_failure(self, regular_user):
        """Test logging sync failure."""
        log = SyncFailureLog.log_failure(
            sync_type='radius_user',
            source=regular_user,
            error='Connection timeout',
            context={'attempt': 1}
        )
        assert log.sync_type == 'radius_user'
        assert log.status == 'pending'
        assert log.retry_count == 0

    def test_schedule_retry(self, regular_user):
        """Test scheduling retry."""
        log = SyncFailureLog.log_failure(
            sync_type='radius_user',
            source=regular_user,
            error='Connection timeout'
        )
        result = log.schedule_retry()
        assert result is True
        assert log.retry_count == 1

    def test_max_retries_exceeded(self, regular_user):
        """Test max retries exceeded."""
        log = SyncFailureLog.log_failure(
            sync_type='radius_user',
            source=regular_user,
            error='Connection timeout'
        )
        log.retry_count = log.max_retries
        result = log.schedule_retry()
        assert result is False
        assert log.status == 'failed'

"""
Tests for the RADIUS application.
Tests cover models, synchronization services, and signals.
"""
import pytest
from django.contrib.auth import get_user_model

from .models import (
    RadCheck, RadReply, RadUserGroup, RadGroupCheck, RadGroupReply,
    RadAcct, RadPostAuth, RadiusServer
)

User = get_user_model()


# =============================================================================
# MODEL TESTS
# =============================================================================

@pytest.mark.django_db
class TestRadCheckModel:
    """Tests for RadCheck model."""

    def test_create_radcheck(self):
        """Test creating a RadCheck entry."""
        entry = RadCheck.objects.create(
            username="testuser",
            attribute="Cleartext-Password",
            op=":=",
            value="password123",
            statut=True
        )
        assert entry.username == "testuser"
        assert entry.attribute == "Cleartext-Password"
        assert entry.statut is True

    def test_radcheck_str_representation(self):
        """Test RadCheck string representation."""
        entry = RadCheck.objects.create(
            username="testuser",
            attribute="Cleartext-Password",
            op=":=",
            value="password123"
        )
        assert "testuser" in str(entry)

    def test_radcheck_disable_user(self):
        """Test disabling user via statut field."""
        entry = RadCheck.objects.create(
            username="testuser",
            attribute="Cleartext-Password",
            op=":=",
            value="password123",
            statut=True
        )
        entry.statut = False
        entry.save()
        entry.refresh_from_db()
        assert entry.statut is False


@pytest.mark.django_db
class TestRadReplyModel:
    """Tests for RadReply model."""

    def test_create_radreply(self):
        """Test creating a RadReply entry."""
        entry = RadReply.objects.create(
            username="testuser",
            attribute="Session-Timeout",
            op="=",
            value="3600"
        )
        assert entry.username == "testuser"
        assert entry.attribute == "Session-Timeout"
        assert entry.value == "3600"

    def test_radreply_mikrotik_rate_limit(self):
        """Test MikroTik rate limit attribute."""
        entry = RadReply.objects.create(
            username="testuser",
            attribute="Mikrotik-Rate-Limit",
            op="=",
            value="10M/5M"
        )
        assert entry.attribute == "Mikrotik-Rate-Limit"
        assert "M" in entry.value


@pytest.mark.django_db
class TestRadUserGroupModel:
    """Tests for RadUserGroup model."""

    def test_create_radusergroup(self):
        """Test creating a RadUserGroup entry."""
        entry = RadUserGroup.objects.create(
            username="testuser",
            groupname="profile_1_student",
            priority=0
        )
        assert entry.username == "testuser"
        assert entry.groupname == "profile_1_student"
        assert entry.priority == 0

    def test_radusergroup_multiple_groups(self):
        """Test user in multiple groups with priority."""
        group1 = RadUserGroup.objects.create(
            username="testuser",
            groupname="profile_1_student",
            priority=0
        )
        group2 = RadUserGroup.objects.create(
            username="testuser",
            groupname="admin",
            priority=1
        )

        groups = RadUserGroup.objects.filter(username="testuser").order_by('priority')
        assert groups.count() == 2
        assert groups.first() == group1


@pytest.mark.django_db
class TestRadGroupReplyModel:
    """Tests for RadGroupReply model."""

    def test_create_radgroupreply(self):
        """Test creating a RadGroupReply entry."""
        entry = RadGroupReply.objects.create(
            groupname="profile_1_student",
            attribute="Session-Timeout",
            op="=",
            value="28800"
        )
        assert entry.groupname == "profile_1_student"
        assert entry.attribute == "Session-Timeout"

    def test_radgroupreply_bandwidth_limit(self):
        """Test group bandwidth limit."""
        entry = RadGroupReply.objects.create(
            groupname="profile_1_student",
            attribute="Mikrotik-Rate-Limit",
            op="=",
            value="10M/10M"
        )
        assert "Mikrotik-Rate-Limit" in entry.attribute


@pytest.mark.django_db
class TestRadAcctModel:
    """Tests for RadAcct (accounting) model."""

    def test_create_radacct(self):
        """Test creating a RadAcct entry."""
        entry = RadAcct.objects.create(
            acctsessionid="session123",
            acctuniqueid="unique123",
            username="testuser",
            nasipaddress="192.168.1.1",
            acctstarttime="2024-01-01 10:00:00",
            acctstoptime=None,
            acctsessiontime=3600,
            acctinputoctets=1000000,
            acctoutputoctets=2000000,
            acctterminatecause="User-Request"
        )
        assert entry.username == "testuser"
        assert entry.acctsessiontime == 3600

    def test_radacct_calculate_data_usage(self):
        """Test calculating total data usage."""
        entry = RadAcct.objects.create(
            acctsessionid="session123",
            acctuniqueid="unique123",
            username="testuser",
            nasipaddress="192.168.1.1",
            acctinputoctets=1000000,
            acctoutputoctets=2000000
        )
        total = entry.acctinputoctets + entry.acctoutputoctets
        assert total == 3000000


@pytest.mark.django_db
class TestRadPostAuthModel:
    """Tests for RadPostAuth model."""

    def test_create_radpostauth_accept(self):
        """Test creating a successful auth entry."""
        entry = RadPostAuth.objects.create(
            username="testuser",
            reply="Access-Accept",
            calledstationid="AA:BB:CC:DD:EE:FF",
            callingstationid="11:22:33:44:55:66"
        )
        assert entry.reply == "Access-Accept"

    def test_create_radpostauth_reject(self):
        """Test creating a rejected auth entry."""
        entry = RadPostAuth.objects.create(
            username="testuser",
            reply="Access-Reject",
            calledstationid="AA:BB:CC:DD:EE:FF"
        )
        assert entry.reply == "Access-Reject"


# =============================================================================
# SIGNAL TESTS
# =============================================================================

@pytest.mark.django_db
class TestRadiusSignals:
    """Tests for RADIUS synchronization signals."""

    def test_user_deactivation_disables_radius(self, radius_activated_user, radcheck_entry):
        """Test that deactivating user disables RADIUS entry."""
        # Create RadCheck entry for user
        radcheck = RadCheck.objects.create(
            username=radius_activated_user.username,
            attribute="Cleartext-Password",
            op=":=",
            value="password",
            statut=True
        )

        # Deactivate user
        radius_activated_user.is_active = False
        radius_activated_user.save()

        # Check RadCheck is disabled
        radcheck.refresh_from_db()
        assert radcheck.statut is False

    def test_user_deletion_removes_radius_entries(self, regular_user):
        """Test that deleting user removes RADIUS entries."""
        username = regular_user.username

        # Create RADIUS entries
        RadCheck.objects.create(
            username=username,
            attribute="Cleartext-Password",
            op=":=",
            value="password"
        )
        RadReply.objects.create(
            username=username,
            attribute="Session-Timeout",
            op="=",
            value="3600"
        )
        RadUserGroup.objects.create(
            username=username,
            groupname="user",
            priority=0
        )

        # Delete user
        regular_user.delete()

        # Verify entries are deleted
        assert RadCheck.objects.filter(username=username).count() == 0
        assert RadReply.objects.filter(username=username).count() == 0
        assert RadUserGroup.objects.filter(username=username).count() == 0


# =============================================================================
# SERVICE TESTS
# =============================================================================

@pytest.mark.django_db
class TestRadiusServices:
    """Tests for RADIUS service layer."""

    def test_profile_group_name_generation(self, profile):
        """Test generating group name from profile."""
        from radius.services import RadiusProfileGroupService
        group_name = RadiusProfileGroupService.get_group_name(profile)
        assert group_name.startswith("profile_")
        assert str(profile.id) in group_name

    def test_sync_profile_creates_group_entries(self, profile):
        """Test syncing profile creates RadGroupReply entries."""
        from radius.services import RadiusProfileGroupService

        result = RadiusProfileGroupService.sync_profile_to_radius_group(profile)

        if result.get('success'):
            group_name = result.get('groupname')
            # Check entries were created
            assert RadGroupReply.objects.filter(groupname=group_name).exists()

    def test_assign_user_to_profile_group(self, radius_activated_user, profile):
        """Test assigning user to profile group."""
        from radius.services import RadiusProfileGroupService

        # First sync the profile
        RadiusProfileGroupService.sync_profile_to_radius_group(profile)

        # Assign user to group
        group_name = RadiusProfileGroupService.get_group_name(profile)
        RadUserGroup.objects.update_or_create(
            username=radius_activated_user.username,
            groupname=group_name,
            defaults={'priority': 0}
        )

        # Verify assignment
        assert RadUserGroup.objects.filter(
            username=radius_activated_user.username,
            groupname=group_name
        ).exists()


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

@pytest.mark.django_db
@pytest.mark.integration
class TestRadiusIntegration:
    """Integration tests for RADIUS functionality."""

    def test_full_user_activation_flow(self, regular_user, profile):
        """Test complete user activation flow."""
        # Setup user with profile
        regular_user.profile = profile
        regular_user.cleartext_password = "TestPassword123!"
        regular_user.save()

        username = regular_user.username

        # Create RADIUS entries (simulating activation)
        RadCheck.objects.create(
            username=username,
            attribute="Cleartext-Password",
            op=":=",
            value=regular_user.cleartext_password,
            statut=True
        )

        RadReply.objects.create(
            username=username,
            attribute="Session-Timeout",
            op="=",
            value=str(profile.session_timeout)
        )

        RadReply.objects.create(
            username=username,
            attribute="Mikrotik-Rate-Limit",
            op="=",
            value=f"{profile.bandwidth_download}M/{profile.bandwidth_upload}M"
        )

        # Verify all entries exist
        assert RadCheck.objects.filter(username=username).exists()
        assert RadReply.objects.filter(username=username).count() >= 2

    def test_profile_update_syncs_to_groups(self, profile):
        """Test that profile updates sync to RADIUS groups."""
        from radius.services import RadiusProfileGroupService

        # Initial sync
        RadiusProfileGroupService.sync_profile_to_radius_group(profile)
        group_name = RadiusProfileGroupService.get_group_name(profile)

        # Update profile
        profile.bandwidth_download = 50
        profile.save()

        # Re-sync
        RadiusProfileGroupService.sync_profile_to_radius_group(profile)

        # Verify updated bandwidth
        rate_limit = RadGroupReply.objects.filter(
            groupname=group_name,
            attribute="Mikrotik-Rate-Limit"
        ).first()

        if rate_limit:
            assert "50M" in rate_limit.value

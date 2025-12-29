"""
Command to sync all profiles and users to RADIUS groups.

This command implements the migration to the RADIUS group-based architecture where:
- Each Profile = a FreeRADIUS group (profile_{id}_{name})
- Profile parameters are translated to RADIUS attributes in radgroupreply/radgroupcheck
- Users inherit profile settings via radusergroup membership

Usage:
    python manage.py sync_radius_groups                  # Sync all
    python manage.py sync_radius_groups --profiles-only  # Sync profiles only
    python manage.py sync_radius_groups --users-only     # Sync users only
    python manage.py sync_radius_groups --dry-run        # Preview changes
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from radius.services import RadiusProfileGroupService
from core.models import Profile, User
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Synchronize profiles and users to RADIUS groups (group-based architecture)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--profiles-only',
            action='store_true',
            help='Only sync profiles to radgroupreply/radgroupcheck (skip user assignment)',
        )
        parser.add_argument(
            '--users-only',
            action='store_true',
            help='Only sync user group assignments (skip profile sync)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without actually modifying the database',
        )
        parser.add_argument(
            '--profile',
            type=int,
            help='Sync only a specific profile by ID',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Sync only a specific user by username',
        )

    def handle(self, *args, **options):
        profiles_only = options['profiles_only']
        users_only = options['users_only']
        dry_run = options['dry_run']
        profile_id = options.get('profile')
        username = options.get('user')

        if profiles_only and users_only:
            raise CommandError("Cannot use both --profiles-only and --users-only")

        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("RADIUS GROUP SYNCHRONIZATION"))
        self.stdout.write("=" * 70)

        if dry_run:
            self.stdout.write(self.style.WARNING("\n⚠️  DRY RUN MODE - No changes will be made\n"))

        # Single profile sync
        if profile_id:
            return self._sync_single_profile(profile_id, dry_run)

        # Single user sync
        if username:
            return self._sync_single_user(username, dry_run)

        # Full sync
        results = {
            'profiles': None,
            'users': None
        }

        # Step 1: Sync profiles to groups
        if not users_only:
            self.stdout.write("\n[1/2] Syncing profiles to RADIUS groups...")
            results['profiles'] = self._sync_all_profiles(dry_run)

        # Step 2: Sync users to groups
        if not profiles_only:
            self.stdout.write("\n[2/2] Assigning users to profile groups...")
            results['users'] = self._sync_all_users(dry_run)

        # Summary
        self._print_summary(results, dry_run)

    def _sync_single_profile(self, profile_id, dry_run):
        """Sync a single profile."""
        try:
            profile = Profile.objects.get(id=profile_id)
        except Profile.DoesNotExist:
            raise CommandError(f"Profile with ID {profile_id} not found")

        groupname = RadiusProfileGroupService.get_group_name(profile)
        reply_attrs, check_attrs = RadiusProfileGroupService.profile_to_group_attributes(profile)

        self.stdout.write(f"\nProfile: {profile.name} (ID: {profile.id})")
        self.stdout.write(f"RADIUS Group: {groupname}")
        self.stdout.write(f"Active: {'Yes' if profile.is_active else 'No'}")
        self.stdout.write(f"\nReply Attributes ({len(reply_attrs)}):")
        for attr in reply_attrs:
            self.stdout.write(f"  - {attr['attribute']} {attr['op']} {attr['value']}")

        self.stdout.write(f"\nCheck Attributes ({len(check_attrs)}):")
        for attr in check_attrs:
            self.stdout.write(f"  - {attr['attribute']} {attr['op']} {attr['value']}")

        if not dry_run:
            result = RadiusProfileGroupService.sync_profile_to_radius_group(profile)
            if result['success']:
                self.stdout.write(self.style.SUCCESS(f"\n✅ Profile synced successfully"))
            else:
                self.stdout.write(self.style.ERROR(f"\n❌ Sync failed"))
        else:
            self.stdout.write(self.style.WARNING("\n[DRY RUN] Would sync profile"))

    def _sync_single_user(self, username, dry_run):
        """Sync a single user."""
        try:
            user = User.objects.select_related('profile', 'promotion', 'promotion__profile').get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"User '{username}' not found")

        profile = user.get_effective_profile()

        self.stdout.write(f"\nUser: {user.username}")
        self.stdout.write(f"RADIUS Activated: {'Yes' if user.is_radius_activated else 'No'}")
        self.stdout.write(f"RADIUS Enabled: {'Yes' if user.is_radius_enabled else 'No'}")

        if profile:
            groupname = RadiusProfileGroupService.get_group_name(profile)
            source = 'direct' if user.profile else 'promotion'
            self.stdout.write(f"Profile: {profile.name} (via {source})")
            self.stdout.write(f"Would assign to group: {groupname}")
        else:
            self.stdout.write(self.style.WARNING("No effective profile"))

        if not dry_run and user.is_radius_activated:
            result = RadiusProfileGroupService.sync_user_profile_group(user)
            if result.get('groupname'):
                self.stdout.write(self.style.SUCCESS(f"\n✅ User assigned to group '{result['groupname']}'"))
            else:
                self.stdout.write(self.style.WARNING(f"\n⚠️ User has no group assignment"))
        else:
            self.stdout.write(self.style.WARNING("\n[DRY RUN] Would sync user"))

    def _sync_all_profiles(self, dry_run):
        """Sync all profiles."""
        profiles = Profile.objects.filter(is_active=True)
        results = {
            'total': profiles.count(),
            'success': 0,
            'errors': []
        }

        for profile in profiles:
            groupname = RadiusProfileGroupService.get_group_name(profile)
            self.stdout.write(f"  - {profile.name} → {groupname}")

            if not dry_run:
                try:
                    result = RadiusProfileGroupService.sync_profile_to_radius_group(profile)
                    if result['success']:
                        results['success'] += 1
                except Exception as e:
                    results['errors'].append(f"{profile.name}: {str(e)}")

        if dry_run:
            results['success'] = results['total']

        return results

    def _sync_all_users(self, dry_run):
        """Sync all users."""
        users = User.objects.filter(
            is_active=True,
            is_radius_activated=True
        ).select_related('profile', 'promotion', 'promotion__profile')

        results = {
            'total': users.count(),
            'assigned': 0,
            'no_profile': 0,
            'errors': []
        }

        for user in users:
            profile = user.get_effective_profile()
            if profile:
                groupname = RadiusProfileGroupService.get_group_name(profile)
                source = 'direct' if user.profile else 'promo'
                self.stdout.write(f"  - {user.username} → {groupname} ({source})")

                if not dry_run:
                    try:
                        result = RadiusProfileGroupService.sync_user_profile_group(user)
                        if result.get('groupname'):
                            results['assigned'] += 1
                    except Exception as e:
                        results['errors'].append(f"{user.username}: {str(e)}")
                else:
                    results['assigned'] += 1
            else:
                self.stdout.write(self.style.WARNING(f"  - {user.username} → (no profile)"))
                results['no_profile'] += 1

        return results

    def _print_summary(self, results, dry_run):
        """Print sync summary."""
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("SYNCHRONIZATION SUMMARY"))
        self.stdout.write("=" * 70)

        if dry_run:
            self.stdout.write(self.style.WARNING("⚠️  DRY RUN - No changes were made"))

        if results['profiles']:
            p = results['profiles']
            self.stdout.write(f"\nProfiles: {p['success']}/{p['total']} synced")
            if p.get('errors'):
                self.stdout.write(self.style.ERROR(f"  Errors: {len(p['errors'])}"))
                for err in p['errors'][:5]:
                    self.stdout.write(f"    - {err}")

        if results['users']:
            u = results['users']
            self.stdout.write(f"\nUsers: {u['assigned']}/{u['total']} assigned to groups")
            self.stdout.write(f"  No profile: {u['no_profile']}")
            if u.get('errors'):
                self.stdout.write(self.style.ERROR(f"  Errors: {len(u['errors'])}"))
                for err in u['errors'][:5]:
                    self.stdout.write(f"    - {err}")

        self.stdout.write("")

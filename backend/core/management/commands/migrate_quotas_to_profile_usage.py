"""
Management command to migrate data from UserQuota to UserProfileUsage.
This is a one-time migration to transition from the old quota system
to the new profile-based usage tracking system.

Usage:
  python manage.py migrate_quotas_to_profile_usage --dry-run  # Preview
  python manage.py migrate_quotas_to_profile_usage             # Execute
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import UserQuota, UserProfileUsage, User


class Command(BaseCommand):
    help = 'Migrate data from UserQuota to UserProfileUsage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually migrating',
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip users that already have a UserProfileUsage entry',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        skip_existing = options['skip_existing']

        if dry_run:
            self.stdout.write(
                self.style.WARNING('\n=== DRY RUN MODE - No changes will be made ===\n')
            )

        # Get all UserQuota entries
        quotas = UserQuota.objects.all()

        self.stdout.write(
            self.style.SUCCESS(f'Found {quotas.count()} UserQuota entries to migrate')
        )

        migrated_count = 0
        skipped_count = 0
        error_count = 0

        for quota in quotas:
            try:
                # Check if UserProfileUsage already exists
                existing_usage = UserProfileUsage.objects.filter(user=quota.user).first()

                if existing_usage and skip_existing:
                    self.stdout.write(
                        f'  ⊘ Skipped {quota.user.username} - already has UserProfileUsage'
                    )
                    skipped_count += 1
                    continue

                # Get user's effective profile
                profile = quota.user.get_effective_profile()

                if not profile:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠ Warning: User {quota.user.username} has no profile. '
                            f'UserProfileUsage will be created but may not function correctly.'
                        )
                    )

                if not dry_run:
                    with transaction.atomic():
                        # Create or update UserProfileUsage
                        usage, created = UserProfileUsage.objects.update_or_create(
                            user=quota.user,
                            defaults={
                                'used_today': quota.used_today,
                                'used_week': quota.used_week,
                                'used_month': quota.used_month,
                                'used_total': quota.used_month,  # Use monthly as approximate total
                                'last_daily_reset': quota.last_daily_reset,
                                'last_weekly_reset': quota.last_weekly_reset,
                                'last_monthly_reset': quota.last_monthly_reset,
                                'activation_date': quota.created_at,  # Use quota creation date
                                'is_exceeded': quota.is_exceeded,
                                'is_active': quota.is_active,
                            }
                        )

                        action = 'Created' if created else 'Updated'
                        self.stdout.write(
                            f'  ✓ {action} UserProfileUsage for {quota.user.username}'
                        )
                        self.stdout.write(
                            f'    - Today: {usage.used_today_gb} Go'
                        )
                        self.stdout.write(
                            f'    - Week: {usage.used_week_gb} Go'
                        )
                        self.stdout.write(
                            f'    - Month: {usage.used_month_gb} Go'
                        )
                        self.stdout.write(
                            f'    - Total: {usage.used_total_gb} Go'
                        )
                        self.stdout.write(
                            f'    - Profile: {profile.name if profile else "None"}'
                        )

                        migrated_count += 1
                else:
                    # Dry run - just show what would happen
                    self.stdout.write(
                        f'  [DRY RUN] Would migrate UserQuota for {quota.user.username}:'
                    )
                    self.stdout.write(
                        f'    - Today: {round(quota.used_today / (1024**3), 2)} Go'
                    )
                    self.stdout.write(
                        f'    - Week: {round(quota.used_week / (1024**3), 2)} Go'
                    )
                    self.stdout.write(
                        f'    - Month: {round(quota.used_month / (1024**3), 2)} Go'
                    )
                    self.stdout.write(
                        f'    - Profile: {profile.name if profile else "None"}'
                    )
                    migrated_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ Error migrating {quota.user.username}: {str(e)}'
                    )
                )
                error_count += 1

        # Summary
        self.stdout.write('\n' + '='*60)
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n[DRY RUN] Would have migrated: {migrated_count} quotas'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Successfully migrated: {migrated_count} quotas'
                )
            )

        if skipped_count > 0:
            self.stdout.write(
                self.style.WARNING(f'⊘ Skipped: {skipped_count} (already existed)')
            )

        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(f'✗ Errors: {error_count}')
            )

        # Post-migration instructions
        if not dry_run and migrated_count > 0:
            self.stdout.write('\n' + '='*60)
            self.stdout.write(
                self.style.SUCCESS('\n✅ Migration completed successfully!')
            )
            self.stdout.write('\nNext steps:')
            self.stdout.write('  1. Verify UserProfileUsage data in Django admin')
            self.stdout.write('  2. Test the new profile-based quota system')
            self.stdout.write('  3. Once verified, you can optionally delete old UserQuota entries:')
            self.stdout.write('     python manage.py shell')
            self.stdout.write('     >>> from core.models import UserQuota')
            self.stdout.write('     >>> UserQuota.objects.all().delete()')
            self.stdout.write('')
        elif dry_run:
            self.stdout.write('\n' + '='*60)
            self.stdout.write(
                self.style.SUCCESS('\n✓ Dry run completed!')
            )
            self.stdout.write('\nTo actually perform the migration, run:')
            self.stdout.write('  python manage.py migrate_quotas_to_profile_usage')
            self.stdout.write('')

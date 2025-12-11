"""
Management command to reset daily quotas for all active users.
Should be run daily at midnight via cron.

Example crontab entry:
0 0 * * * cd /path/to/backend && python manage.py reset_daily_quotas
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import UserProfileUsage


class Command(BaseCommand):
    help = 'Reset daily quotas for all active users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be reset without actually resetting',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # Get all active profile usages
        usages = UserProfileUsage.objects.filter(is_active=True)

        self.stdout.write(
            self.style.SUCCESS(f'Found {usages.count()} active user profile usages')
        )

        reset_count = 0
        for usage in usages:
            # Check if daily reset is needed (more than 24 hours since last reset)
            time_since_reset = timezone.now() - usage.last_daily_reset

            if time_since_reset.total_seconds() >= 86400:  # 24 hours
                if not dry_run:
                    usage.reset_daily()
                    self.stdout.write(
                        f'  ✓ Reset daily quota for user: {usage.user.username} '
                        f'({usage.used_today_gb} Go → 0 Go)'
                    )
                else:
                    self.stdout.write(
                        f'  [DRY RUN] Would reset daily quota for user: {usage.user.username} '
                        f'({usage.used_today_gb} Go → 0 Go)'
                    )
                reset_count += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'\n[DRY RUN] Would have reset {reset_count} daily quotas')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Successfully reset {reset_count} daily quotas')
            )

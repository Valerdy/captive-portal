"""
Management command to reset weekly quotas for all active users.
Should be run weekly (e.g., every Monday at midnight) via cron.

Example crontab entry:
0 0 * * 1 cd /path/to/backend && python manage.py reset_weekly_quotas
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import UserProfileUsage


class Command(BaseCommand):
    help = 'Reset weekly quotas for all active users'

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
            # Check if weekly reset is needed (more than 7 days since last reset)
            time_since_reset = timezone.now() - usage.last_weekly_reset

            if time_since_reset.total_seconds() >= 604800:  # 7 days
                if not dry_run:
                    usage.reset_weekly()
                    self.stdout.write(
                        f'  ✓ Reset weekly quota for user: {usage.user.username} '
                        f'({usage.used_week_gb} Go → 0 Go)'
                    )
                else:
                    self.stdout.write(
                        f'  [DRY RUN] Would reset weekly quota for user: {usage.user.username} '
                        f'({usage.used_week_gb} Go → 0 Go)'
                    )
                reset_count += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'\n[DRY RUN] Would have reset {reset_count} weekly quotas')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Successfully reset {reset_count} weekly quotas')
            )

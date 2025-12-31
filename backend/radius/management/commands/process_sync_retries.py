"""
Management command to process pending RADIUS sync retries.

Usage:
    python manage.py process_sync_retries
    python manage.py process_sync_retries --sync-type radius_user
    python manage.py process_sync_retries --cleanup --days 30
"""
from django.core.management.base import BaseCommand

from radius.retry_service import RadiusSyncRetryService


class Command(BaseCommand):
    help = 'Process pending RADIUS synchronization retries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sync-type',
            type=str,
            choices=['radius_user', 'radius_profile', 'radius_group'],
            help='Filter by sync type'
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up old resolved/failed failures'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to keep resolved failures (default: 30)'
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show failure statistics'
        )

    def handle(self, *args, **options):
        sync_type = options.get('sync_type')
        cleanup = options.get('cleanup')
        days = options.get('days')
        stats = options.get('stats')

        if stats:
            self._show_statistics()
            return

        if cleanup:
            self._cleanup_old_failures(days)
            return

        self._process_retries(sync_type)

    def _process_retries(self, sync_type=None):
        """Process pending retries."""
        self.stdout.write("Processing pending RADIUS sync retries...")

        if sync_type:
            self.stdout.write(f"  Filtering by sync type: {sync_type}")

        results = RadiusSyncRetryService.process_pending_retries(sync_type)

        self.stdout.write("")
        self.stdout.write("Results:")
        self.stdout.write(f"  Processed: {results['processed']}")
        self.stdout.write(self.style.SUCCESS(
            f"  Succeeded: {results['succeeded']}"
        ))
        self.stdout.write(self.style.WARNING(
            f"  Failed (will retry): {results['failed']}"
        ))
        self.stdout.write(self.style.ERROR(
            f"  Permanent failures: {results['permanent_failures']}"
        ))

        if results['processed'] == 0:
            self.stdout.write("")
            self.stdout.write("No pending retries to process.")

    def _cleanup_old_failures(self, days):
        """Clean up old failure logs."""
        self.stdout.write(f"Cleaning up failures older than {days} days...")

        deleted = RadiusSyncRetryService.cleanup_old_failures(days)

        if deleted:
            self.stdout.write(self.style.SUCCESS(
                f"Deleted {deleted} old failure records."
            ))
        else:
            self.stdout.write("No old records to clean up.")

    def _show_statistics(self):
        """Show failure statistics."""
        stats = RadiusSyncRetryService.get_failure_statistics()

        self.stdout.write("")
        self.stdout.write("RADIUS Sync Failure Statistics")
        self.stdout.write("=" * 50)
        self.stdout.write("")

        self.stdout.write("By Status:")
        for status, count in stats['by_status'].items():
            self.stdout.write(f"  {status}: {count}")

        self.stdout.write("")
        self.stdout.write("By Sync Type:")
        for sync_type, statuses in stats['by_type'].items():
            self.stdout.write(f"  {sync_type}:")
            for status, count in statuses.items():
                self.stdout.write(f"    {status}: {count}")

        self.stdout.write("")
        self.stdout.write(f"Total Pending: {stats['total_pending']}")
        self.stdout.write(f"Total Failed: {stats['total_failed']}")

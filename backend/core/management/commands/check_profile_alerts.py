"""
Management command to check profile alerts and trigger notifications.
Should be run periodically (e.g., every hour) via cron.

Example crontab entry:
0 * * * * cd /path/to/backend && python manage.py check_profile_alerts
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from core.models import UserProfileUsage, ProfileAlert


class Command(BaseCommand):
    help = 'Check profile alerts and send notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what alerts would trigger without actually sending notifications',
        )
        parser.add_argument(
            '--send-email',
            action='store_true',
            help='Actually send email notifications (requires EMAIL settings)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        send_email = options['send_email']

        # Get all active alerts
        alerts = ProfileAlert.objects.filter(is_active=True).select_related('profile')

        self.stdout.write(
            self.style.SUCCESS(f'Checking {alerts.count()} active alerts...')
        )

        # Get all active profile usages
        usages = UserProfileUsage.objects.filter(is_active=True).select_related('user')

        triggered_alerts = []

        for usage in usages:
            profile = usage.get_effective_profile()
            if not profile:
                continue

            # Get alerts for this profile
            profile_alerts = alerts.filter(profile=profile)

            for alert in profile_alerts:
                if alert.should_trigger(usage):
                    triggered_alerts.append({
                        'alert': alert,
                        'usage': usage,
                        'user': usage.user,
                        'profile': profile
                    })

        self.stdout.write(
            self.style.WARNING(f'\n⚠ Found {len(triggered_alerts)} triggered alerts')
        )

        # Process triggered alerts
        for item in triggered_alerts:
            alert = item['alert']
            usage = item['usage']
            user = item['user']
            profile = item['profile']

            # Format message
            message = self._format_alert_message(alert, usage)

            self.stdout.write(f'\n  Alert: {alert.get_alert_type_display()}')
            self.stdout.write(f'  User: {user.username} ({user.email})')
            self.stdout.write(f'  Profile: {profile.name}')
            self.stdout.write(f'  Message: {message}')

            if not dry_run and send_email and user.email:
                try:
                    self._send_notification(alert, user, message)
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Notification sent to {user.email}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ✗ Failed to send notification: {str(e)}'))
            elif dry_run:
                self.stdout.write(f'  [DRY RUN] Would send notification to {user.email}')

        summary_msg = f'\n{"[DRY RUN] " if dry_run else ""}Processed {len(triggered_alerts)} triggered alerts'
        if dry_run:
            self.stdout.write(self.style.WARNING(summary_msg))
        else:
            self.stdout.write(self.style.SUCCESS(summary_msg))

    def _format_alert_message(self, alert, usage):
        """Format alert message with user data"""
        if alert.message_template:
            return alert.message_template.format(
                username=usage.user.username,
                percent=round(usage.total_usage_percent, 2),
                remaining_gb=round(
                    (usage.get_effective_profile().data_volume - usage.used_total) / (1024**3),
                    2
                ) if usage.get_effective_profile() else 0,
                days_remaining=usage.days_remaining() or 0
            )
        else:
            # Default message
            if alert.alert_type in ['quota_warning', 'quota_critical']:
                return f"Attention: {round(usage.total_usage_percent, 2)}% de votre quota utilisé"
            else:
                return f"Votre profil expire dans {usage.days_remaining()} jour(s)"

    def _send_notification(self, alert, user, message):
        """Send notification based on notification method"""
        if alert.notification_method in ['email', 'all']:
            subject = f'Alerte profil: {alert.get_alert_type_display()}'
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

        # TODO: Add SMS notification support
        # TODO: Add system notification support

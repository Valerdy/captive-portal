# Generated manually for performance optimization
# Adds indexes for frequently queried fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_add_audit_and_sync_failure_logs'),
    ]

    operations = [
        # User model indexes
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['is_radius_activated', 'is_radius_enabled'], name='core_user_radius_status_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['promotion', 'is_active'], name='core_user_promotion_active_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['is_active', 'is_radius_activated'], name='core_user_active_radius_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['profile', 'is_active'], name='core_user_profile_active_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['date_joined'], name='core_user_date_joined_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['email'], name='core_user_email_idx'),
        ),

        # Device model indexes
        migrations.AddIndex(
            model_name='device',
            index=models.Index(fields=['user', 'is_active'], name='core_device_user_active_idx'),
        ),
        migrations.AddIndex(
            model_name='device',
            index=models.Index(fields=['last_seen'], name='core_device_last_seen_idx'),
        ),

        # Session model indexes
        migrations.AddIndex(
            model_name='session',
            index=models.Index(fields=['status', 'start_time'], name='core_session_status_time_idx'),
        ),
        migrations.AddIndex(
            model_name='session',
            index=models.Index(fields=['user', 'status'], name='core_session_user_status_idx'),
        ),

        # Voucher model indexes
        migrations.AddIndex(
            model_name='voucher',
            index=models.Index(fields=['status', 'valid_until'], name='core_voucher_status_valid_idx'),
        ),
        migrations.AddIndex(
            model_name='voucher',
            index=models.Index(fields=['created_by', 'created_at'], name='core_voucher_created_idx'),
        ),

        # UserQuota model indexes
        migrations.AddIndex(
            model_name='userquota',
            index=models.Index(fields=['is_exceeded', 'is_active'], name='core_userquota_exceeded_idx'),
        ),

        # UserProfileUsage model indexes
        migrations.AddIndex(
            model_name='userprofileusage',
            index=models.Index(fields=['is_exceeded', 'is_active'], name='core_usage_exceeded_idx'),
        ),
        migrations.AddIndex(
            model_name='userprofileusage',
            index=models.Index(fields=['activation_date'], name='core_usage_activation_idx'),
        ),

        # ProfileHistory model indexes
        migrations.AddIndex(
            model_name='profilehistory',
            index=models.Index(fields=['user', '-changed_at'], name='core_history_user_date_idx'),
        ),
        migrations.AddIndex(
            model_name='profilehistory',
            index=models.Index(fields=['changed_by', '-changed_at'], name='core_history_changed_idx'),
        ),
    ]

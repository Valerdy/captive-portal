"""
Retry mechanism service for RADIUS synchronization.

This service handles automatic retry of failed RADIUS synchronizations
with exponential backoff, logging, and error tracking.
"""
import logging
import traceback
from datetime import timedelta
from functools import wraps
from typing import Callable, Any, Optional, Dict, List

from django.utils import timezone
from django.db import transaction

from core.models import SyncFailureLog, User, Profile

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY_SECONDS = 120  # 2 minutes
DEFAULT_MAX_DELAY_SECONDS = 3600  # 1 hour
BACKOFF_MULTIPLIER = 2


# =============================================================================
# Retry Decorator
# =============================================================================

def with_retry(
    sync_type: str,
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: int = DEFAULT_BASE_DELAY_SECONDS,
    log_failure: bool = True
):
    """
    Decorator to add retry functionality to sync functions.

    Args:
        sync_type: Type of synchronization (e.g., 'radius_user', 'radius_profile')
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds between retries
        log_failure: Whether to log failures to SyncFailureLog

    Usage:
        @with_retry(sync_type='radius_user')
        def sync_user_to_radius(user):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Dict[str, Any]:
            source = args[0] if args else kwargs.get('source')
            attempt = 0
            last_error = None

            while attempt <= max_retries:
                try:
                    result = func(*args, **kwargs)

                    # If successful, mark any pending failures as resolved
                    if result.get('success') and source:
                        _mark_pending_failures_resolved(sync_type, source)

                    return result

                except Exception as e:
                    attempt += 1
                    last_error = e
                    error_message = str(e)
                    tb = traceback.format_exc()

                    logger.warning(
                        "Sync failed (attempt %d/%d) for %s: %s",
                        attempt, max_retries + 1, sync_type, error_message
                    )

                    if attempt <= max_retries:
                        # Calculate delay with exponential backoff
                        delay = min(
                            base_delay * (BACKOFF_MULTIPLIER ** (attempt - 1)),
                            DEFAULT_MAX_DELAY_SECONDS
                        )
                        logger.info("Retrying in %d seconds...", delay)

                        # For synchronous execution, we don't actually wait
                        # The retry will be scheduled via Celery or management command

                    if log_failure and source:
                        _log_sync_failure(
                            sync_type=sync_type,
                            source=source,
                            error=error_message,
                            traceback_str=tb,
                            attempt=attempt,
                            max_retries=max_retries
                        )

            # All retries exhausted
            logger.error(
                "Sync permanently failed after %d attempts for %s: %s",
                max_retries + 1, sync_type, str(last_error)
            )

            return {
                'success': False,
                'error': str(last_error),
                'attempts': attempt,
                'permanent_failure': True
            }

        return wrapper
    return decorator


# =============================================================================
# Failure Logging
# =============================================================================

def _log_sync_failure(
    sync_type: str,
    source: Any,
    error: str,
    traceback_str: str = None,
    attempt: int = 1,
    max_retries: int = DEFAULT_MAX_RETRIES
) -> SyncFailureLog:
    """Log a synchronization failure."""
    context = {
        'attempt': attempt,
        'max_retries': max_retries,
        'timestamp': timezone.now().isoformat()
    }

    # Check if there's already a pending failure for this source
    existing = SyncFailureLog.objects.filter(
        sync_type=sync_type,
        source_model=source.__class__.__name__,
        source_id=source.pk,
        status__in=['pending', 'retrying']
    ).first()

    if existing:
        # Update existing failure
        existing.retry_count = attempt
        existing.error_message = error
        existing.error_traceback = traceback_str
        existing.context = context
        existing.schedule_retry()
        return existing

    # Create new failure log
    return SyncFailureLog.log_failure(
        sync_type=sync_type,
        source=source,
        error=error,
        context=context,
        traceback_str=traceback_str
    )


def _mark_pending_failures_resolved(sync_type: str, source: Any) -> int:
    """Mark all pending failures for a source as resolved."""
    updated = SyncFailureLog.objects.filter(
        sync_type=sync_type,
        source_model=source.__class__.__name__,
        source_id=source.pk,
        status__in=['pending', 'retrying']
    ).update(
        status='resolved',
        resolved_at=timezone.now()
    )
    return updated


# =============================================================================
# Retry Service Class
# =============================================================================

class RadiusSyncRetryService:
    """
    Service for managing and processing RADIUS sync retries.
    """

    @staticmethod
    def get_pending_retries(
        sync_type: str = None,
        limit: int = 100
    ) -> List[SyncFailureLog]:
        """
        Get pending sync failures that are due for retry.

        Args:
            sync_type: Filter by sync type (optional)
            limit: Maximum number of failures to return
        """
        queryset = SyncFailureLog.objects.filter(
            status='pending',
            next_retry_at__lte=timezone.now()
        )

        if sync_type:
            queryset = queryset.filter(sync_type=sync_type)

        return list(queryset.order_by('next_retry_at')[:limit])

    @staticmethod
    def process_pending_retries(sync_type: str = None) -> Dict[str, int]:
        """
        Process all pending retries that are due.

        Returns:
            Dict with counts of processed, succeeded, and failed retries
        """
        from .services import RadiusProfileGroupService

        pending = RadiusSyncRetryService.get_pending_retries(sync_type)
        results = {
            'processed': 0,
            'succeeded': 0,
            'failed': 0,
            'permanent_failures': 0
        }

        for failure in pending:
            results['processed'] += 1

            try:
                with transaction.atomic():
                    # Mark as retrying
                    failure.status = 'retrying'
                    failure.save()

                    # Get the source object
                    source = RadiusSyncRetryService._get_source_object(failure)

                    if source is None:
                        logger.warning(
                            "Source object not found for failure %d, marking as ignored",
                            failure.id
                        )
                        failure.mark_ignored()
                        continue

                    # Attempt the sync based on type
                    result = RadiusSyncRetryService._retry_sync(
                        failure.sync_type,
                        source
                    )

                    if result.get('success'):
                        failure.mark_resolved()
                        results['succeeded'] += 1
                        logger.info(
                            "Retry succeeded for %s (%s)",
                            failure.source_repr, failure.sync_type
                        )
                    else:
                        if failure.schedule_retry():
                            results['failed'] += 1
                            logger.warning(
                                "Retry failed for %s, scheduled next attempt",
                                failure.source_repr
                            )
                        else:
                            results['permanent_failures'] += 1
                            logger.error(
                                "Retry permanently failed for %s (max retries exceeded)",
                                failure.source_repr
                            )

            except Exception as e:
                logger.exception(
                    "Error processing retry for failure %d: %s",
                    failure.id, str(e)
                )
                failure.schedule_retry()
                results['failed'] += 1

        return results

    @staticmethod
    def _get_source_object(failure: SyncFailureLog) -> Optional[Any]:
        """Get the source object from a failure log."""
        model_map = {
            'User': User,
            'Profile': Profile,
        }

        model_class = model_map.get(failure.source_model)
        if not model_class:
            return None

        try:
            return model_class.objects.get(pk=failure.source_id)
        except model_class.DoesNotExist:
            return None

    @staticmethod
    def _retry_sync(sync_type: str, source: Any) -> Dict[str, Any]:
        """Execute the appropriate sync based on type."""
        from .services import RadiusProfileGroupService

        if sync_type == 'radius_user':
            return RadiusSyncRetryService._sync_user(source)
        elif sync_type == 'radius_profile':
            return RadiusProfileGroupService.sync_profile_to_radius_group(source)
        elif sync_type == 'radius_group':
            return RadiusSyncRetryService._sync_user_group(source)
        else:
            return {'success': False, 'error': f'Unknown sync type: {sync_type}'}

    @staticmethod
    def _sync_user(user: User) -> Dict[str, Any]:
        """Sync a single user to RADIUS."""
        from .models import RadCheck, RadReply, RadUserGroup

        try:
            if not user.is_radius_activated:
                return {'success': False, 'error': 'User not activated'}

            if not user.cleartext_password:
                return {'success': False, 'error': 'No cleartext password'}

            # Update/create RadCheck entry
            RadCheck.objects.update_or_create(
                username=user.username,
                attribute='Cleartext-Password',
                defaults={
                    'op': ':=',
                    'value': user.cleartext_password,
                    'statut': user.is_radius_enabled
                }
            )

            # Get effective profile
            profile = user.get_effective_profile()
            if profile:
                # Update session timeout
                RadReply.objects.update_or_create(
                    username=user.username,
                    attribute='Session-Timeout',
                    defaults={
                        'op': '=',
                        'value': str(profile.session_timeout)
                    }
                )

                # Update rate limit
                RadReply.objects.update_or_create(
                    username=user.username,
                    attribute='Mikrotik-Rate-Limit',
                    defaults={
                        'op': '=',
                        'value': f"{profile.bandwidth_download}M/{profile.bandwidth_upload}M"
                    }
                )

            return {'success': True}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _sync_user_group(user: User) -> Dict[str, Any]:
        """Sync user's group membership to RADIUS."""
        from .models import RadUserGroup
        from .services import RadiusProfileGroupService

        try:
            profile = user.get_effective_profile()
            if not profile:
                return {'success': False, 'error': 'No effective profile'}

            group_name = RadiusProfileGroupService.get_group_name(profile)

            # Remove old group memberships
            RadUserGroup.objects.filter(
                username=user.username,
                groupname__startswith='profile_'
            ).delete()

            # Add to new group
            RadUserGroup.objects.update_or_create(
                username=user.username,
                groupname=group_name,
                defaults={'priority': 0}
            )

            return {'success': True, 'groupname': group_name}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def cleanup_old_failures(days: int = 30) -> int:
        """
        Clean up resolved/ignored failures older than specified days.

        Args:
            days: Number of days to keep resolved failures

        Returns:
            Number of deleted records
        """
        cutoff = timezone.now() - timedelta(days=days)
        deleted, _ = SyncFailureLog.objects.filter(
            status__in=['resolved', 'ignored', 'failed'],
            created_at__lt=cutoff
        ).delete()

        if deleted:
            logger.info("Cleaned up %d old sync failure logs", deleted)

        return deleted

    @staticmethod
    def get_failure_statistics() -> Dict[str, Any]:
        """Get statistics about sync failures."""
        from django.db.models import Count

        stats = SyncFailureLog.objects.values('sync_type', 'status').annotate(
            count=Count('id')
        )

        result = {
            'by_type': {},
            'by_status': {},
            'total_pending': 0,
            'total_failed': 0
        }

        for stat in stats:
            sync_type = stat['sync_type']
            status = stat['status']
            count = stat['count']

            if sync_type not in result['by_type']:
                result['by_type'][sync_type] = {}
            result['by_type'][sync_type][status] = count

            if status not in result['by_status']:
                result['by_status'][status] = 0
            result['by_status'][status] += count

            if status == 'pending':
                result['total_pending'] += count
            elif status == 'failed':
                result['total_failed'] += count

        return result


# =============================================================================
# Management Command Helper
# =============================================================================

def run_pending_retries(sync_type: str = None) -> Dict[str, int]:
    """
    Run pending retries (for use in management commands).

    Usage:
        python manage.py shell
        >>> from radius.retry_service import run_pending_retries
        >>> run_pending_retries()
    """
    return RadiusSyncRetryService.process_pending_retries(sync_type)

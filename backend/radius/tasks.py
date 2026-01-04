"""
Tâches Celery pour la gestion des quotas, synchronisation RADIUS et notifications.

Ces tâches sont exécutées automatiquement via Celery Beat.
Voir backend/celery.py pour la configuration des schedules.

Pour démarrer Celery:
    celery -A backend worker -l info -Q quotas,sync,notifications,maintenance
    celery -A backend beat -l info

Alternative sans Celery (crontab):
    # Vérifier les quotas toutes les 5 minutes
    */5 * * * * cd /path/to/project && python manage.py check_quotas

    # Reset journalier à minuit
    0 0 * * * cd /path/to/project && python manage.py reset_daily_quotas
"""

from celery import shared_task
from django.db import models, transaction
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Tâches de gestion des quotas
# =============================================================================

@shared_task(
    bind=True,
    name='radius.tasks.check_and_enforce_quotas',
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True
)
def check_and_enforce_quotas(self):
    """
    Vérifie tous les utilisateurs actifs et désactive ceux qui ont dépassé leurs quotas.

    Cette tâche doit être exécutée régulièrement (toutes les 5-10 minutes).
    """
    from .services import QuotaEnforcementService

    logger.info("Starting quota enforcement check...")

    try:
        # D'abord synchroniser les données depuis radacct
        sync_result = QuotaEnforcementService.sync_usage_from_radacct()
        logger.info(f"Usage sync: {sync_result['updated']} users updated")

        # Ensuite appliquer les quotas
        result = QuotaEnforcementService.enforce_quotas()

        logger.info(
            f"Quota enforcement complete: "
            f"{result['disabled_quota']} disabled for quota, "
            f"{result['disabled_validity']} disabled for validity expiry"
        )

        return result

    except Exception as e:
        logger.error(f"Error during quota enforcement: {e}")
        raise


@shared_task(
    bind=True,
    name='radius.tasks.reset_daily_quotas',
    max_retries=3,
    default_retry_delay=300
)
def reset_daily_quotas(self):
    """
    Réinitialise les compteurs de quota journaliers pour tous les utilisateurs.

    Cette tâche doit être exécutée une fois par jour à minuit.
    """
    from core.models import UserProfileUsage

    logger.info("Resetting daily quotas...")

    try:
        count = UserProfileUsage.objects.filter(is_active=True).update(
            used_today=0,
            last_daily_reset=timezone.now()
        )

        logger.info(f"Reset daily quotas for {count} users")
        return {'reset_count': count}

    except Exception as e:
        logger.error(f"Error resetting daily quotas: {e}")
        raise


@shared_task(
    bind=True,
    name='radius.tasks.reset_weekly_quotas',
    max_retries=3,
    default_retry_delay=300
)
def reset_weekly_quotas(self):
    """
    Réinitialise les compteurs de quota hebdomadaires pour tous les utilisateurs.

    Cette tâche doit être exécutée une fois par semaine (le lundi à minuit).
    """
    from core.models import UserProfileUsage

    logger.info("Resetting weekly quotas...")

    try:
        count = UserProfileUsage.objects.filter(is_active=True).update(
            used_week=0,
            last_weekly_reset=timezone.now()
        )

        logger.info(f"Reset weekly quotas for {count} users")
        return {'reset_count': count}

    except Exception as e:
        logger.error(f"Error resetting weekly quotas: {e}")
        raise


@shared_task(
    bind=True,
    name='radius.tasks.reset_monthly_quotas',
    max_retries=3,
    default_retry_delay=300
)
def reset_monthly_quotas(self):
    """
    Réinitialise les compteurs de quota mensuels pour tous les utilisateurs.

    Cette tâche doit être exécutée une fois par mois (le 1er à minuit).
    """
    from core.models import UserProfileUsage

    logger.info("Resetting monthly quotas...")

    try:
        count = UserProfileUsage.objects.filter(is_active=True).update(
            used_month=0,
            last_monthly_reset=timezone.now()
        )

        logger.info(f"Reset monthly quotas for {count} users")
        return {'reset_count': count}

    except Exception as e:
        logger.error(f"Error resetting monthly quotas: {e}")
        raise


# =============================================================================
# Tâches de synchronisation RADIUS
# =============================================================================

@shared_task(
    bind=True,
    name='radius.tasks.sync_profiles_to_radius',
    max_retries=3,
    default_retry_delay=60
)
def sync_profiles_to_radius(self):
    """
    Synchronise tous les profils modifiés vers RADIUS.

    Cette tâche peut être exécutée après des modifications de profils en masse.
    """
    from core.models import User, Profile
    from .services import ProfileRadiusService

    logger.info("Syncing all profiles to RADIUS...")

    try:
        users = User.objects.filter(
            is_radius_activated=True,
            is_radius_enabled=True
        ).select_related('profile', 'promotion__profile')

        synced = 0
        errors = []

        for user in users:
            profile = user.get_effective_profile()
            if profile:
                try:
                    ProfileRadiusService.sync_user_to_radius(user, profile)
                    synced += 1
                except Exception as e:
                    errors.append({
                        'user': user.username,
                        'error': str(e)
                    })

        logger.info(f"Synced {synced} users to RADIUS, {len(errors)} errors")
        return {
            'synced': synced,
            'errors': errors
        }

    except Exception as e:
        logger.error(f"Error syncing profiles to RADIUS: {e}")
        raise


@shared_task(
    bind=True,
    name='radius.tasks.check_expired_profiles',
    max_retries=3,
    default_retry_delay=300
)
def check_expired_profiles(self):
    """
    Vérifie et désactive les utilisateurs dont le profil a expiré.

    Cette tâche peut être combinée avec check_and_enforce_quotas ou exécutée séparément.
    """
    from core.models import User
    from .services import ProfileRadiusService, QuotaEnforcementService

    logger.info("Checking for expired profiles...")

    try:
        users = User.objects.filter(
            is_radius_activated=True,
            is_radius_enabled=True
        ).select_related('profile', 'promotion__profile', 'profile_usage')

        expired_count = 0

        for user in users:
            validity_status = QuotaEnforcementService.check_user_validity(user)
            if validity_status['expired']:
                ProfileRadiusService.deactivate_user_radius(user, reason='validity_expired')
                expired_count += 1

        logger.info(f"Disabled {expired_count} users with expired profiles")
        return {'expired_count': expired_count}

    except Exception as e:
        logger.error(f"Error checking expired profiles: {e}")
        raise


# =============================================================================
# Tâche de retry automatique des syncs échouées
# =============================================================================

@shared_task(
    bind=True,
    name='radius.tasks.retry_failed_syncs',
    max_retries=1
)
def retry_failed_syncs(self):
    """
    Retente les synchronisations échouées (RADIUS et MikroTik).

    Cette tâche traite les entrées dans SyncFailureLog qui sont:
    - En statut 'pending'
    - Dont next_retry_at est passé
    - Qui n'ont pas atteint max_retries

    Backoff exponentiel: 2min, 4min, 8min, 16min, 32min...
    """
    from core.models import SyncFailureLog, User, Profile
    from .services import ProfileRadiusService, RadiusProfileGroupService

    logger.info("Starting retry of failed syncs...")

    now = timezone.now()
    pending_failures = SyncFailureLog.objects.filter(
        status='pending',
        next_retry_at__lte=now,
        retry_count__lt=models.F('max_retries')
    ).select_for_update(skip_locked=True)[:50]  # Traiter max 50 à la fois

    results = {
        'processed': 0,
        'success': 0,
        'failed': 0,
        'details': []
    }

    for failure in pending_failures:
        results['processed'] += 1
        failure.status = 'retrying'
        failure.save(update_fields=['status'])

        try:
            success = _retry_sync_failure(failure)

            if success:
                failure.mark_resolved()
                results['success'] += 1
                logger.info(f"Retry successful: {failure}")
            else:
                failure.schedule_retry()
                results['failed'] += 1
                logger.warning(f"Retry failed, rescheduled: {failure}")

            results['details'].append({
                'id': failure.id,
                'type': failure.sync_type,
                'source': failure.source_repr,
                'success': success
            })

        except Exception as e:
            failure.schedule_retry()
            results['failed'] += 1
            logger.error(f"Error retrying {failure}: {e}")

    logger.info(
        f"Retry complete: {results['success']}/{results['processed']} successful, "
        f"{results['failed']} rescheduled"
    )

    return results


def _retry_sync_failure(failure) -> bool:
    """
    Exécute le retry pour un échec de synchronisation spécifique.

    Returns:
        True si le retry a réussi, False sinon
    """
    from core.models import User, Profile, BlockedSite
    from .services import ProfileRadiusService, RadiusProfileGroupService

    try:
        # Récupérer l'objet source
        if failure.source_model == 'User':
            source = User.objects.get(pk=failure.source_id)
        elif failure.source_model == 'Profile':
            source = Profile.objects.get(pk=failure.source_id)
        elif failure.source_model == 'BlockedSite':
            source = BlockedSite.objects.get(pk=failure.source_id)
        else:
            logger.warning(f"Unknown source model: {failure.source_model}")
            return False

        # Exécuter le retry selon le type
        if failure.sync_type == 'radius_user':
            if isinstance(source, User) and source.is_radius_activated:
                ProfileRadiusService.sync_user_to_radius(source)
                return True

        elif failure.sync_type == 'radius_group':
            if isinstance(source, User) and source.is_radius_activated:
                RadiusProfileGroupService.sync_user_profile_group(source)
                return True

        elif failure.sync_type == 'radius_profile':
            if isinstance(source, Profile) and source.is_radius_enabled:
                RadiusProfileGroupService.sync_profile_to_radius_group(source)
                return True

        elif failure.sync_type == 'mikrotik_user':
            from mikrotik.profile_service import MikrotikProfileSyncService
            if isinstance(source, User):
                service = MikrotikProfileSyncService()
                if service.router:
                    service.sync_user(source)
                    return True

        elif failure.sync_type == 'mikrotik_dns':
            from mikrotik.dns_service import MikrotikDNSBlockingService
            if isinstance(source, BlockedSite) and source.is_active:
                service = MikrotikDNSBlockingService()
                result = service.update_blocked_domain(source)
                return result.get('success', False)

        return False

    except Exception as e:
        logger.error(f"Error in retry execution: {e}")
        return False


# =============================================================================
# Tâches de notifications
# =============================================================================

@shared_task(
    bind=True,
    name='radius.tasks.send_quota_alerts',
    max_retries=3,
    default_retry_delay=120
)
def send_quota_alerts(self):
    """
    Envoie des alertes pour les utilisateurs approchant leurs limites de quota.

    Cette tâche vérifie les seuils d'alerte définis dans ProfileAlert
    et envoie les notifications via le service approprié.
    """
    from core.models import User, ProfileAlert, UserProfileUsage
    from core.services.notifications import NotificationService

    logger.info("Checking quota alerts...")

    try:
        # Récupérer toutes les alertes actives
        alerts = ProfileAlert.objects.filter(is_active=True).select_related('profile')

        triggered_alerts = []
        notifications_sent = 0

        for alert in alerts:
            # Récupérer les utilisateurs avec ce profil
            users = User.objects.filter(
                is_radius_activated=True,
                is_radius_enabled=True
            ).filter(
                models.Q(profile=alert.profile) |
                models.Q(promotion__profile=alert.profile)
            ).select_related('profile_usage', 'profile', 'promotion__profile')

            for user in users:
                usage = getattr(user, 'profile_usage', None)
                if usage and alert.should_trigger(usage):
                    # Éviter les doublons d'alertes
                    alert_key = f"{user.id}_{alert.id}_{alert.alert_type}"
                    if _should_send_alert(alert_key, alert):
                        triggered_alerts.append({
                            'user': user.username,
                            'email': user.email,
                            'alert_type': alert.alert_type,
                            'threshold': alert.threshold_percent,
                            'notification_method': alert.notification_method
                        })

                        # Envoyer la notification
                        try:
                            NotificationService.send_alert(
                                user=user,
                                alert=alert,
                                usage=usage
                            )
                            notifications_sent += 1
                            _mark_alert_sent(alert_key)
                        except Exception as e:
                            logger.error(f"Failed to send alert to {user.username}: {e}")

        logger.info(
            f"Quota alerts: {len(triggered_alerts)} triggered, "
            f"{notifications_sent} notifications sent"
        )

        return {
            'triggered_alerts': triggered_alerts,
            'notifications_sent': notifications_sent
        }

    except Exception as e:
        logger.error(f"Error sending quota alerts: {e}")
        raise


def _should_send_alert(alert_key: str, alert) -> bool:
    """
    Vérifie si une alerte doit être envoyée (évite les doublons).

    Utilise le cache Django pour tracker les alertes déjà envoyées.
    """
    from django.core.cache import cache

    cache_key = f"alert_sent_{alert_key}"
    if cache.get(cache_key):
        return False

    return True


def _mark_alert_sent(alert_key: str):
    """Marque une alerte comme envoyée dans le cache."""
    from django.core.cache import cache

    cache_key = f"alert_sent_{alert_key}"
    # Cache pour 6 heures pour éviter le spam
    cache.set(cache_key, True, timeout=21600)


@shared_task(
    bind=True,
    name='radius.tasks.send_notification',
    max_retries=3,
    default_retry_delay=60
)
def send_notification(self, user_id: int, notification_type: str, context: dict = None):
    """
    Envoie une notification à un utilisateur spécifique.

    Args:
        user_id: ID de l'utilisateur
        notification_type: Type de notification (quota_warning, quota_exceeded, etc.)
        context: Contexte additionnel pour le template
    """
    from core.models import User
    from core.services.notifications import NotificationService

    try:
        user = User.objects.get(pk=user_id)

        NotificationService.send_notification(
            user=user,
            notification_type=notification_type,
            context=context or {}
        )

        logger.info(f"Notification '{notification_type}' sent to {user.username}")
        return {'success': True, 'user': user.username}

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'success': False, 'error': 'User not found'}
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise


# =============================================================================
# Tâches de maintenance
# =============================================================================

@shared_task(
    bind=True,
    name='radius.tasks.cleanup_old_disconnection_logs',
    max_retries=1
)
def cleanup_old_disconnection_logs(self, days: int = 90):
    """
    Nettoie les anciens logs de déconnexion.

    Args:
        days: Nombre de jours de rétention (défaut: 90)
    """
    from core.models import UserDisconnectionLog

    logger.info(f"Cleaning up disconnection logs older than {days} days...")

    try:
        cutoff_date = timezone.now() - timedelta(days=days)
        deleted, _ = UserDisconnectionLog.objects.filter(
            disconnected_at__lt=cutoff_date,
            is_active=False
        ).delete()

        logger.info(f"Deleted {deleted} old disconnection logs")
        return {'deleted': deleted}

    except Exception as e:
        logger.error(f"Error cleaning up disconnection logs: {e}")
        raise


@shared_task(
    bind=True,
    name='radius.tasks.cleanup_old_sync_failures',
    max_retries=1
)
def cleanup_old_sync_failures(self, days: int = 30):
    """
    Nettoie les anciens logs d'échecs de synchronisation résolus.

    Args:
        days: Nombre de jours de rétention (défaut: 30)
    """
    from core.models import SyncFailureLog

    logger.info(f"Cleaning up resolved sync failures older than {days} days...")

    try:
        cutoff_date = timezone.now() - timedelta(days=days)
        deleted, _ = SyncFailureLog.objects.filter(
            status__in=['resolved', 'ignored', 'failed'],
            created_at__lt=cutoff_date
        ).delete()

        logger.info(f"Deleted {deleted} old sync failure logs")
        return {'deleted': deleted}

    except Exception as e:
        logger.error(f"Error cleaning up sync failures: {e}")
        raise

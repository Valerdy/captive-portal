"""
Tâches Celery pour la gestion des quotas et la synchronisation RADIUS.

Ces tâches sont exécutées automatiquement via Celery Beat:
- Vérification des quotas toutes les 5 minutes
- Traitement des retries de synchronisation toutes les 2 minutes
- Reset des quotas journaliers/hebdomadaires/mensuels
- Nettoyage des anciens logs

Pour exécuter manuellement:
    from radius.tasks import check_and_enforce_quotas_task
    check_and_enforce_quotas_task.delay()
"""

from celery import shared_task
from django.db import models, transaction
from django.utils import timezone
from datetime import timedelta
import logging
import traceback

logger = logging.getLogger(__name__)


# =============================================================================
# Tâches de synchronisation RADIUS avec retry
# =============================================================================

@shared_task(
    bind=True,
    name='radius.tasks.process_sync_retries_task',
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
)
def process_sync_retries_task(self):
    """
    Traite les échecs de synchronisation en attente de retry.

    Cette tâche récupère tous les SyncFailureLog avec:
    - status = 'pending'
    - next_retry_at <= maintenant
    - retry_count < max_retries

    Et tente de les resynchroniser.
    """
    from core.models import SyncFailureLog, User, Profile, BlockedSite
    from .services import RadiusProfileGroupService

    logger.info("Processing sync retries...")

    now = timezone.now()

    # Récupérer les échecs à retenter
    pending_retries = SyncFailureLog.objects.filter(
        status='pending',
        next_retry_at__lte=now,
        retry_count__lt=models.F('max_retries')
    ).order_by('next_retry_at')[:50]  # Limiter à 50 par batch

    results = {
        'processed': 0,
        'resolved': 0,
        'failed': 0,
        'errors': []
    }

    for failure in pending_retries:
        results['processed'] += 1

        try:
            # Marquer comme en cours de retry
            failure.status = 'retrying'
            failure.save(update_fields=['status'])

            success = False

            # Déterminer le type de sync et réessayer
            if failure.sync_type == 'radius_user':
                success = _retry_radius_user_sync(failure)
            elif failure.sync_type == 'radius_profile':
                success = _retry_radius_profile_sync(failure)
            elif failure.sync_type == 'radius_group':
                success = _retry_radius_group_sync(failure)
            elif failure.sync_type == 'mikrotik_user':
                success = _retry_mikrotik_user_sync(failure)
            elif failure.sync_type == 'mikrotik_dns':
                success = _retry_mikrotik_dns_sync(failure)
            else:
                logger.warning(f"Unknown sync type: {failure.sync_type}")
                failure.mark_ignored()
                continue

            if success:
                failure.mark_resolved()
                results['resolved'] += 1
                logger.info(f"Successfully resolved sync failure {failure.id}: {failure.source_repr}")
            else:
                # Planifier le prochain retry
                if not failure.schedule_retry():
                    results['failed'] += 1
                    logger.warning(f"Max retries reached for sync failure {failure.id}")

        except Exception as e:
            # Mettre à jour le message d'erreur et planifier retry
            failure.error_message = str(e)
            failure.error_traceback = traceback.format_exc()
            failure.schedule_retry()
            results['errors'].append({
                'id': failure.id,
                'error': str(e)
            })
            logger.error(f"Error retrying sync failure {failure.id}: {e}")

    logger.info(
        f"Sync retry processing complete: "
        f"{results['processed']} processed, "
        f"{results['resolved']} resolved, "
        f"{results['failed']} failed permanently"
    )

    return results


def _retry_radius_user_sync(failure):
    """Retente la synchronisation d'un utilisateur vers RADIUS."""
    from core.models import User
    from .services import RadiusUserService

    try:
        user = User.objects.get(pk=failure.source_id)
        if user.is_radius_activated and user.is_radius_enabled:
            RadiusUserService.sync_user_to_radius(user)
            return True
        else:
            # L'utilisateur n'est plus actif, ignorer
            return True
    except User.DoesNotExist:
        # L'utilisateur a été supprimé, considérer comme résolu
        return True
    except Exception:
        raise


def _retry_radius_profile_sync(failure):
    """Retente la synchronisation d'un profil vers RADIUS."""
    from core.models import Profile
    from .services import RadiusProfileGroupService

    try:
        profile = Profile.objects.get(pk=failure.source_id)
        if profile.is_active and profile.is_radius_enabled:
            result = RadiusProfileGroupService.sync_profile_to_radius_group(profile)
            return result.get('success', False)
        else:
            return True
    except Profile.DoesNotExist:
        return True
    except Exception:
        raise


def _retry_radius_group_sync(failure):
    """Retente l'association utilisateur-groupe RADIUS."""
    from core.models import User
    from .models import RadUserGroup

    try:
        user = User.objects.get(pk=failure.source_id)
        profile = user.get_effective_profile()

        if not user.is_radius_activated or not profile:
            return True

        # Supprimer les anciennes associations et recréer
        RadUserGroup.objects.filter(username=user.username).delete()

        if profile.radius_group_name:
            RadUserGroup.objects.create(
                username=user.username,
                groupname=profile.radius_group_name,
                priority=0
            )

        return True
    except User.DoesNotExist:
        return True
    except Exception:
        raise


def _retry_mikrotik_user_sync(failure):
    """Retente la synchronisation d'un utilisateur vers MikroTik."""
    from core.models import User
    from mikrotik.services import MikrotikHotspotService

    try:
        user = User.objects.get(pk=failure.source_id)
        if user.is_radius_activated and user.is_radius_enabled:
            MikrotikHotspotService.sync_user(user)
            return True
        return True
    except User.DoesNotExist:
        return True
    except Exception:
        raise


def _retry_mikrotik_dns_sync(failure):
    """Retente la synchronisation d'un site bloqué vers MikroTik DNS."""
    from core.models import BlockedSite
    from mikrotik.services import MikrotikDnsService

    try:
        site = BlockedSite.objects.get(pk=failure.source_id)
        if site.is_active:
            MikrotikDnsService.sync_blocked_site(site)
            return True
        return True
    except BlockedSite.DoesNotExist:
        return True
    except Exception:
        raise


@shared_task(
    bind=True,
    name='radius.tasks.sync_user_to_radius_async',
    max_retries=5,
    default_retry_delay=30,
)
def sync_user_to_radius_async(self, user_id):
    """
    Synchronise un utilisateur vers RADIUS de manière asynchrone.
    Utilisé par les signaux pour éviter de bloquer les requêtes.
    """
    from core.models import User, SyncFailureLog
    from .services import RadiusUserService

    try:
        user = User.objects.select_related('profile', 'promotion__profile').get(pk=user_id)

        if not user.is_radius_activated:
            return {'status': 'skipped', 'reason': 'User not activated'}

        RadiusUserService.sync_user_to_radius(user)
        return {'status': 'success', 'user': user.username}

    except User.DoesNotExist:
        return {'status': 'skipped', 'reason': 'User not found'}

    except Exception as e:
        logger.error(f"Error syncing user {user_id} to RADIUS: {e}")

        # Log l'échec pour retry ultérieur
        try:
            user = User.objects.get(pk=user_id)
            SyncFailureLog.log_failure(
                sync_type='radius_user',
                source=user,
                error=e,
                traceback_str=traceback.format_exc()
            )
        except User.DoesNotExist:
            pass

        # Retry avec Celery
        raise self.retry(exc=e)


# =============================================================================
# Tâches de gestion des quotas
# =============================================================================

@shared_task(
    bind=True,
    name='radius.tasks.check_and_enforce_quotas_task',
    max_retries=3,
)
def check_and_enforce_quotas_task(self):
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
        raise self.retry(exc=e)


@shared_task(name='radius.tasks.reset_daily_quotas_task')
def reset_daily_quotas_task():
    """
    Réinitialise les compteurs de quota journaliers pour tous les utilisateurs.
    Cette tâche doit être exécutée une fois par jour à minuit.
    """
    from core.models import UserProfileUsage

    logger.info("Resetting daily quotas...")

    try:
        with transaction.atomic():
            count = UserProfileUsage.objects.filter(is_active=True).update(
                used_today=0,
                last_daily_reset=timezone.now()
            )

        logger.info(f"Reset daily quotas for {count} users")
        return {'reset_count': count}

    except Exception as e:
        logger.error(f"Error resetting daily quotas: {e}")
        raise


@shared_task(name='radius.tasks.reset_weekly_quotas_task')
def reset_weekly_quotas_task():
    """
    Réinitialise les compteurs de quota hebdomadaires pour tous les utilisateurs.
    Cette tâche doit être exécutée une fois par semaine (le lundi à minuit).
    """
    from core.models import UserProfileUsage

    logger.info("Resetting weekly quotas...")

    try:
        with transaction.atomic():
            count = UserProfileUsage.objects.filter(is_active=True).update(
                used_week=0,
                last_weekly_reset=timezone.now()
            )

        logger.info(f"Reset weekly quotas for {count} users")
        return {'reset_count': count}

    except Exception as e:
        logger.error(f"Error resetting weekly quotas: {e}")
        raise


@shared_task(name='radius.tasks.reset_monthly_quotas_task')
def reset_monthly_quotas_task():
    """
    Réinitialise les compteurs de quota mensuels pour tous les utilisateurs.
    Cette tâche doit être exécutée une fois par mois (le 1er à minuit).
    """
    from core.models import UserProfileUsage

    logger.info("Resetting monthly quotas...")

    try:
        with transaction.atomic():
            count = UserProfileUsage.objects.filter(is_active=True).update(
                used_month=0,
                last_monthly_reset=timezone.now()
            )

        logger.info(f"Reset monthly quotas for {count} users")
        return {'reset_count': count}

    except Exception as e:
        logger.error(f"Error resetting monthly quotas: {e}")
        raise


@shared_task(name='radius.tasks.check_expired_profiles_task')
def check_expired_profiles_task():
    """
    Vérifie et désactive les utilisateurs dont le profil a expiré.
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
# Tâches de nettoyage
# =============================================================================

@shared_task(name='radius.tasks.cleanup_old_logs_task')
def cleanup_old_logs_task(days: int = 90):
    """
    Nettoie les anciens logs de déconnexion et échecs de synchronisation.

    Cette tâche traite les entrées dans SyncFailureLog qui sont:
    - En statut 'pending'
    - Dont next_retry_at est passé
    - Qui n'ont pas atteint max_retries

    Backoff exponentiel: 2min, 4min, 8min, 16min, 32min...
    """
    from core.models import UserDisconnectionLog, SyncFailureLog, AdminAuditLog

    logger.info(f"Cleaning up logs older than {days} days...")

    try:
        cutoff_date = timezone.now() - timedelta(days=days)
        results = {}

        # Nettoyer les logs de déconnexion résolus
        deleted_disconn, _ = UserDisconnectionLog.objects.filter(
            disconnected_at__lt=cutoff_date,
            is_active=False
        ).delete()
        results['disconnection_logs'] = deleted_disconn

        # Nettoyer les échecs de synchronisation résolus/ignorés
        deleted_sync, _ = SyncFailureLog.objects.filter(
            created_at__lt=cutoff_date,
            status__in=['resolved', 'ignored', 'failed']
        ).delete()
        results['sync_failures'] = deleted_sync

        # Garder les logs d'audit plus longtemps (180 jours)
        audit_cutoff = timezone.now() - timedelta(days=180)
        deleted_audit, _ = AdminAuditLog.objects.filter(
            created_at__lt=audit_cutoff
        ).delete()
        results['audit_logs'] = deleted_audit

        logger.info(
            f"Cleanup complete: "
            f"{deleted_disconn} disconnection logs, "
            f"{deleted_sync} sync failures, "
            f"{deleted_audit} audit logs deleted"
        )

        return results

    except Exception as e:
        logger.error(f"Error cleaning up logs: {e}")
        raise


@shared_task(name='radius.tasks.cleanup_old_radius_sessions_task')
def cleanup_old_radius_sessions_task(days: int = 30):
    """
    Nettoie les anciennes sessions RADIUS terminées.

    Args:
        days: Nombre de jours de rétention (défaut: 30)
    """
    from .models import RadiusAccounting

    logger.info(f"Cleaning up RADIUS sessions older than {days} days...")

    try:
        cutoff_date = timezone.now() - timedelta(days=days)

        deleted, _ = RadiusAccounting.objects.filter(
            timestamp__lt=cutoff_date,
            status_type='stop'
        ).delete()

        logger.info(f"Deleted {deleted} old RADIUS accounting records")
        return {'deleted': deleted}

    except Exception as e:
        logger.error(f"Error cleaning up RADIUS sessions: {e}")
        raise

# =============================================================================
# Tâches de notifications
# =============================================================================

# =============================================================================
# Tâches de synchronisation en masse
# =============================================================================

@shared_task(
    bind=True,
    name='radius.tasks.sync_all_profiles_task',
    max_retries=1,
)
def sync_all_profiles_task(self):
    """
    Synchronise tous les profils actifs vers RADIUS.
    Utilisé pour la synchronisation initiale ou après maintenance.
    """
    from core.models import Profile
    from .services import RadiusProfileGroupService

    logger.info("Syncing all profiles to RADIUS...")

    results = {
        'synced': 0,
        'skipped': 0,
        'errors': []
    }

    try:
        profiles = Profile.objects.filter(
            is_active=True,
            is_radius_enabled=True
        )

        for profile in profiles:
            try:
                result = RadiusProfileGroupService.sync_profile_to_radius_group(profile)
                if result.get('success'):
                    results['synced'] += 1
                else:
                    results['errors'].append({
                        'profile': profile.name,
                        'error': result.get('error', 'Unknown error')
                    })
            except Exception as e:
                results['errors'].append({
                    'profile': profile.name,
                    'error': str(e)
                })

        logger.info(f"Profile sync complete: {results['synced']} synced, {len(results['errors'])} errors")
        return results

    except Exception as e:
        logger.error(f"Error syncing profiles to RADIUS: {e}")
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    name='radius.tasks.sync_all_users_task',
    max_retries=1,
)
def sync_all_users_task(self):
    """
    Synchronise tous les utilisateurs activés vers RADIUS.
    Utilisé pour la synchronisation initiale ou après maintenance.
    """
    from core.models import User
    from .services import RadiusUserService

    logger.info("Syncing all users to RADIUS...")

    results = {
        'synced': 0,
        'skipped': 0,
        'errors': []
    }

    try:
        users = User.objects.filter(
            is_radius_activated=True,
            is_radius_enabled=True
        ).select_related('profile', 'promotion__profile')

        for user in users:
            try:
                RadiusUserService.sync_user_to_radius(user)
                results['synced'] += 1
            except Exception as e:
                results['errors'].append({
                    'user': user.username,
                    'error': str(e)
                })

        logger.info(f"User sync complete: {results['synced']} synced, {len(results['errors'])} errors")
        return results

    except Exception as e:
        logger.error(f"Error syncing users to RADIUS: {e}")
        raise self.retry(exc=e)


# =============================================================================
# Tâches d'alertes
# =============================================================================

@shared_task(name='radius.tasks.send_quota_alerts_task')
def send_quota_alerts_task():
    """
    Envoie des alertes pour les utilisateurs approchant leurs limites de quota.
    Cette tâche vérifie les seuils d'alerte définis dans ProfileAlert.
    """
    from core.models import User, ProfileAlert

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
                    triggered_alerts.append({
                        'user': user.username,
                        'email': user.email,
                        'alert_type': alert.alert_type,
                        'threshold': alert.threshold_percent,
                        'notification_method': alert.notification_method
                    })
                    # TODO: Implémenter l'envoi de notification selon notification_method

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

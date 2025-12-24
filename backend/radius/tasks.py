"""
Tâches périodiques pour la gestion des quotas et la synchronisation RADIUS.

Ces tâches peuvent être exécutées via:
- Celery Beat (recommandé pour production)
- Django-cron
- Crontab système avec manage.py

Exemple crontab:
# Vérifier les quotas toutes les 5 minutes
*/5 * * * * cd /path/to/project && python manage.py check_quotas

# Synchroniser la consommation toutes les 10 minutes
*/10 * * * * cd /path/to/project && python manage.py sync_radius_usage

# Reset journalier à minuit
0 0 * * * cd /path/to/project && python manage.py reset_daily_quotas

# Reset hebdomadaire le lundi à minuit
0 0 * * 1 cd /path/to/project && python manage.py reset_weekly_quotas

# Reset mensuel le 1er du mois à minuit
0 0 1 * * cd /path/to/project && python manage.py reset_monthly_quotas
"""

from django.db import models
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def check_and_enforce_quotas():
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


def reset_daily_quotas():
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


def reset_weekly_quotas():
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


def reset_monthly_quotas():
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


def sync_profiles_to_radius():
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


def check_expired_profiles():
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


def cleanup_old_disconnection_logs(days: int = 90):
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


def send_quota_alerts():
    """
    Envoie des alertes pour les utilisateurs approchant leurs limites de quota.

    Cette tâche vérifie les seuils d'alerte définis dans ProfileAlert.
    """
    from core.models import User, ProfileAlert, UserProfileUsage

    logger.info("Checking quota alerts...")

    try:
        # Récupérer toutes les alertes actives
        alerts = ProfileAlert.objects.filter(is_active=True).select_related('profile')

        triggered_alerts = []

        for alert in alerts:
            # Récupérer les utilisateurs avec ce profil
            users = User.objects.filter(
                is_radius_activated=True,
                is_radius_enabled=True
            ).filter(
                models.Q(profile=alert.profile) |
                models.Q(promotion__profile=alert.profile)
            ).select_related('profile_usage')

            for user in users:
                usage = getattr(user, 'profile_usage', None)
                if usage and alert.should_trigger(usage):
                    triggered_alerts.append({
                        'user': user.username,
                        'alert_type': alert.alert_type,
                        'threshold': alert.threshold_percent
                    })
                    # TODO: Implémenter l'envoi de notification selon notification_method

        logger.info(f"Triggered {len(triggered_alerts)} quota alerts")
        return {'triggered_alerts': triggered_alerts}

    except Exception as e:
        logger.error(f"Error sending quota alerts: {e}")
        raise

"""
Configuration Celery pour le portail captif.

Ce module configure Celery pour exécuter les tâches asynchrones et périodiques:
- Synchronisation RADIUS
- Gestion des quotas
- Retry des échecs de synchronisation
- Nettoyage des logs
"""

import os
from celery import Celery
from celery.schedules import crontab

# Définir le module de settings Django par défaut
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Créer l'application Celery
app = Celery('captive_portal')

# Charger la configuration depuis les settings Django
# Les settings Celery sont préfixés par CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-découverte des tâches dans les apps Django
app.autodiscover_tasks()


# Configuration des tâches périodiques (Celery Beat)
app.conf.beat_schedule = {
    # Vérification des quotas toutes les 5 minutes
    'check-quotas-every-5-minutes': {
        'task': 'radius.tasks.check_and_enforce_quotas_task',
        'schedule': 300.0,  # 5 minutes
    },

    # Traitement des retries de synchronisation toutes les 2 minutes
    'process-sync-retries-every-2-minutes': {
        'task': 'radius.tasks.process_sync_retries_task',
        'schedule': 120.0,  # 2 minutes
    },

    # Reset quotas journaliers à minuit
    'reset-daily-quotas-at-midnight': {
        'task': 'radius.tasks.reset_daily_quotas_task',
        'schedule': crontab(hour=0, minute=0),
    },

    # Reset quotas hebdomadaires le lundi à minuit
    'reset-weekly-quotas-on-monday': {
        'task': 'radius.tasks.reset_weekly_quotas_task',
        'schedule': crontab(day_of_week=1, hour=0, minute=0),
    },

    # Reset quotas mensuels le 1er du mois à minuit
    'reset-monthly-quotas-on-first': {
        'task': 'radius.tasks.reset_monthly_quotas_task',
        'schedule': crontab(day_of_month=1, hour=0, minute=0),
    },

    # Nettoyage des anciens logs tous les jours à 3h du matin
    'cleanup-old-logs-daily': {
        'task': 'radius.tasks.cleanup_old_logs_task',
        'schedule': crontab(hour=3, minute=0),
    },

    # Vérification des profils expirés toutes les heures
    'check-expired-profiles-hourly': {
        'task': 'radius.tasks.check_expired_profiles_task',
        'schedule': 3600.0,  # 1 heure
    },
}

# Configuration du timezone
app.conf.timezone = 'UTC'


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Tâche de debug pour vérifier que Celery fonctionne."""
    print(f'Request: {self.request!r}')

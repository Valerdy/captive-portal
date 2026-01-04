"""
Configuration Celery pour le projet Captive Portal.

Pour démarrer Celery:
    celery -A backend worker -l info
    celery -A backend beat -l info  # Pour les tâches périodiques

Variables d'environnement:
    CELERY_BROKER_URL: URL du broker (défaut: redis://localhost:6379/0)
    CELERY_RESULT_BACKEND: URL du backend de résultats (défaut: redis://localhost:6379/0)
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('backend')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# =============================================================================
# Configuration Celery
# =============================================================================

app.conf.update(
    # Broker (Redis par défaut)
    broker_url=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    result_backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),

    # Sérialiseur
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',

    # Timezone
    timezone='UTC',
    enable_utc=True,

    # Résultats
    result_expires=3600,  # 1 heure

    # Retry par défaut
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,

    # Prefetch (optimisation)
    worker_prefetch_multiplier=1,

    # Concurrence
    worker_concurrency=4,
)

# =============================================================================
# Tâches périodiques (Celery Beat)
# =============================================================================

app.conf.beat_schedule = {
    # Vérifier les quotas toutes les 5 minutes
    'check-quotas-every-5-minutes': {
        'task': 'radius.tasks.check_and_enforce_quotas',
        'schedule': crontab(minute='*/5'),
        'options': {'queue': 'quotas'}
    },

    # Retry des syncs échouées toutes les 2 minutes
    'retry-failed-syncs-every-2-minutes': {
        'task': 'radius.tasks.retry_failed_syncs',
        'schedule': crontab(minute='*/2'),
        'options': {'queue': 'sync'}
    },

    # Envoyer les alertes de quota toutes les 15 minutes
    'send-quota-alerts-every-15-minutes': {
        'task': 'radius.tasks.send_quota_alerts',
        'schedule': crontab(minute='*/15'),
        'options': {'queue': 'notifications'}
    },

    # Reset journalier à minuit
    'reset-daily-quotas-midnight': {
        'task': 'radius.tasks.reset_daily_quotas',
        'schedule': crontab(hour=0, minute=0),
        'options': {'queue': 'quotas'}
    },

    # Reset hebdomadaire le lundi à minuit
    'reset-weekly-quotas-monday': {
        'task': 'radius.tasks.reset_weekly_quotas',
        'schedule': crontab(hour=0, minute=0, day_of_week=1),
        'options': {'queue': 'quotas'}
    },

    # Reset mensuel le 1er à minuit
    'reset-monthly-quotas-first': {
        'task': 'radius.tasks.reset_monthly_quotas',
        'schedule': crontab(hour=0, minute=0, day_of_month=1),
        'options': {'queue': 'quotas'}
    },

    # Vérifier les profils expirés tous les jours à 1h
    'check-expired-profiles-daily': {
        'task': 'radius.tasks.check_expired_profiles',
        'schedule': crontab(hour=1, minute=0),
        'options': {'queue': 'quotas'}
    },

    # Nettoyage des vieux logs tous les dimanches à 3h
    'cleanup-old-logs-weekly': {
        'task': 'radius.tasks.cleanup_old_disconnection_logs',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),
        'args': (90,),  # 90 jours de rétention
        'options': {'queue': 'maintenance'}
    },
}

# Définir les queues
app.conf.task_routes = {
    'radius.tasks.check_and_enforce_quotas': {'queue': 'quotas'},
    'radius.tasks.reset_*': {'queue': 'quotas'},
    'radius.tasks.check_expired_profiles': {'queue': 'quotas'},
    'radius.tasks.sync_*': {'queue': 'sync'},
    'radius.tasks.retry_failed_syncs': {'queue': 'sync'},
    'radius.tasks.send_*': {'queue': 'notifications'},
    'radius.tasks.cleanup_*': {'queue': 'maintenance'},
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Tâche de debug pour vérifier que Celery fonctionne."""
    print(f'Request: {self.request!r}')

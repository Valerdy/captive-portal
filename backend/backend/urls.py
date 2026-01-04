"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse, HttpResponse
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
import time


def api_root(request):
    """API root endpoint"""
    return JsonResponse({
        'message': 'Captive Portal API',
        'version': '1.0.0',
        'endpoints': {
            'admin': '/admin/',
            'api': '/api/',
            'core': '/api/core/',
            'mikrotik': '/api/mikrotik/',
            'radius': '/api/radius/',
            'health': '/api/health/',
            'metrics': '/api/metrics/',
        }
    })


def health_check(request):
    """
    Health check endpoint for Docker/Kubernetes healthchecks.
    Returns 200 if all services are healthy, 503 otherwise.
    """
    health_status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'checks': {}
    }

    # Check database
    try:
        start = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['checks']['database'] = {
            'status': 'healthy',
            'response_time_ms': round((time.time() - start) * 1000, 2)
        }
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }

    # Check Redis/Cache
    try:
        start = time.time()
        cache.set('health_check', 'ok', 10)
        cache_value = cache.get('health_check')
        if cache_value == 'ok':
            health_status['checks']['cache'] = {
                'status': 'healthy',
                'response_time_ms': round((time.time() - start) * 1000, 2)
            }
        else:
            health_status['status'] = 'unhealthy'
            health_status['checks']['cache'] = {
                'status': 'unhealthy',
                'error': 'Cache read/write failed'
            }
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['cache'] = {
            'status': 'unhealthy',
            'error': str(e)
        }

    status_code = 200 if health_status['status'] == 'healthy' else 503
    return JsonResponse(health_status, status=status_code)


def prometheus_metrics(request):
    """
    Prometheus-compatible metrics endpoint.
    Returns metrics in Prometheus text format.
    """
    from core.models import User, Session, Device, Profile, Promotion, SyncFailureLog

    metrics = []

    # Application info
    metrics.append('# HELP captive_portal_info Application info')
    metrics.append('# TYPE captive_portal_info gauge')
    metrics.append('captive_portal_info{version="1.0.0"} 1')

    # User metrics
    try:
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        radius_activated = User.objects.filter(is_radius_activated=True).count()
        radius_enabled = User.objects.filter(is_radius_activated=True, is_radius_enabled=True).count()

        metrics.append('# HELP captive_portal_users_total Total number of users')
        metrics.append('# TYPE captive_portal_users_total gauge')
        metrics.append(f'captive_portal_users_total {total_users}')

        metrics.append('# HELP captive_portal_users_active Number of active users')
        metrics.append('# TYPE captive_portal_users_active gauge')
        metrics.append(f'captive_portal_users_active {active_users}')

        metrics.append('# HELP captive_portal_users_radius_activated Users activated in RADIUS')
        metrics.append('# TYPE captive_portal_users_radius_activated gauge')
        metrics.append(f'captive_portal_users_radius_activated {radius_activated}')

        metrics.append('# HELP captive_portal_users_radius_enabled Users with RADIUS enabled')
        metrics.append('# TYPE captive_portal_users_radius_enabled gauge')
        metrics.append(f'captive_portal_users_radius_enabled {radius_enabled}')
    except Exception:
        pass

    # Session metrics
    try:
        active_sessions = Session.objects.filter(status='active').count()
        total_sessions = Session.objects.count()

        metrics.append('# HELP captive_portal_sessions_active Number of active sessions')
        metrics.append('# TYPE captive_portal_sessions_active gauge')
        metrics.append(f'captive_portal_sessions_active {active_sessions}')

        metrics.append('# HELP captive_portal_sessions_total Total sessions')
        metrics.append('# TYPE captive_portal_sessions_total counter')
        metrics.append(f'captive_portal_sessions_total {total_sessions}')
    except Exception:
        pass

    # Device metrics
    try:
        active_devices = Device.objects.filter(is_active=True).count()
        total_devices = Device.objects.count()

        metrics.append('# HELP captive_portal_devices_active Number of active devices')
        metrics.append('# TYPE captive_portal_devices_active gauge')
        metrics.append(f'captive_portal_devices_active {active_devices}')

        metrics.append('# HELP captive_portal_devices_total Total devices')
        metrics.append('# TYPE captive_portal_devices_total gauge')
        metrics.append(f'captive_portal_devices_total {total_devices}')
    except Exception:
        pass

    # Profile and Promotion metrics
    try:
        total_profiles = Profile.objects.filter(is_active=True).count()
        total_promotions = Promotion.objects.filter(is_active=True).count()

        metrics.append('# HELP captive_portal_profiles_active Active profiles')
        metrics.append('# TYPE captive_portal_profiles_active gauge')
        metrics.append(f'captive_portal_profiles_active {total_profiles}')

        metrics.append('# HELP captive_portal_promotions_active Active promotions')
        metrics.append('# TYPE captive_portal_promotions_active gauge')
        metrics.append(f'captive_portal_promotions_active {total_promotions}')
    except Exception:
        pass

    # Sync failure metrics
    try:
        pending_syncs = SyncFailureLog.objects.filter(status='pending').count()
        failed_syncs = SyncFailureLog.objects.filter(status='failed').count()

        metrics.append('# HELP captive_portal_sync_failures_pending Pending sync retries')
        metrics.append('# TYPE captive_portal_sync_failures_pending gauge')
        metrics.append(f'captive_portal_sync_failures_pending {pending_syncs}')

        metrics.append('# HELP captive_portal_sync_failures_total Permanently failed syncs')
        metrics.append('# TYPE captive_portal_sync_failures_total gauge')
        metrics.append(f'captive_portal_sync_failures_total {failed_syncs}')
    except Exception:
        pass

    # Database connection check
    try:
        start = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_response_time = (time.time() - start) * 1000

        metrics.append('# HELP captive_portal_database_response_ms Database response time in ms')
        metrics.append('# TYPE captive_portal_database_response_ms gauge')
        metrics.append(f'captive_portal_database_response_ms {db_response_time:.2f}')

        metrics.append('# HELP captive_portal_database_up Database availability (1=up, 0=down)')
        metrics.append('# TYPE captive_portal_database_up gauge')
        metrics.append('captive_portal_database_up 1')
    except Exception:
        metrics.append('captive_portal_database_up 0')

    response = HttpResponse('\n'.join(metrics) + '\n', content_type='text/plain; charset=utf-8')
    return response


urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),

    # Health and monitoring endpoints (public)
    path('api/health/', health_check, name='health-check'),
    path('api/metrics/', prometheus_metrics, name='prometheus-metrics'),

    # API endpoints
    path('api/core/', include('core.urls')),
    path('api/mikrotik/', include('mikrotik.urls')),
    path('api/radius/', include('radius.urls')),
]

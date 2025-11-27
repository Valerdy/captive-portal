from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .viewsets import (
    UserViewSet, DeviceViewSet, SessionViewSet, VoucherViewSet,
    BlockedSiteViewSet, UserQuotaViewSet
)
from . import views

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'devices', DeviceViewSet, basename='device')
router.register(r'sessions', SessionViewSet, basename='session')
router.register(r'vouchers', VoucherViewSet, basename='voucher')
router.register(r'blocked-sites', BlockedSiteViewSet, basename='blocked-site')
router.register(r'user-quotas', UserQuotaViewSet, basename='user-quota')

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    path('auth/logout/', views.logout, name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # User profile endpoints
    path('auth/profile/', views.user_profile, name='user_profile'),
    path('auth/profile/update/', views.update_profile, name='update_profile'),
    path('auth/password/change/', views.change_password, name='change_password'),

    # Admin user management endpoints
    path('admin/users/preregister/', views.admin_preregister_user, name='admin_preregister_user'),

    # Admin monitoring endpoints
    path('admin/monitoring/metrics/', views.monitoring_metrics, name='monitoring_metrics'),

    # Router URLs
    path('', include(router.urls)),
]

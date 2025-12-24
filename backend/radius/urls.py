from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import (
    RadiusServerViewSet, RadiusAuthLogViewSet,
    RadiusAccountingViewSet, RadiusClientViewSet,
    RadiusUserViewSet, RadCheckViewSet, RadReplyViewSet,
    RadUserGroupViewSet, RadGroupCheckViewSet, RadGroupReplyViewSet,
    RadPostAuthViewSet, MikrotikIntegrationViewSet
)

router = DefaultRouter()
# Original routes
router.register(r'servers', RadiusServerViewSet, basename='radius-server')
router.register(r'auth-logs', RadiusAuthLogViewSet, basename='auth-log')
router.register(r'accounting', RadiusAccountingViewSet, basename='accounting')
router.register(r'clients', RadiusClientViewSet, basename='radius-client')

# FreeRADIUS user management routes
router.register(r'users', RadiusUserViewSet, basename='radius-user')
router.register(r'radcheck', RadCheckViewSet, basename='radcheck')
router.register(r'radreply', RadReplyViewSet, basename='radreply')
router.register(r'radusergroup', RadUserGroupViewSet, basename='radusergroup')
router.register(r'radgroupcheck', RadGroupCheckViewSet, basename='radgroupcheck')
router.register(r'radgroupreply', RadGroupReplyViewSet, basename='radgroupreply')
router.register(r'radpostauth', RadPostAuthViewSet, basename='radpostauth')

# MikroTik integration routes
router.register(r'mikrotik', MikrotikIntegrationViewSet, basename='mikrotik')

urlpatterns = [
    path('', include(router.urls)),
]

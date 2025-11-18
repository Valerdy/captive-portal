from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import (
    MikrotikRouterViewSet, MikrotikHotspotUserViewSet,
    MikrotikActiveConnectionViewSet, MikrotikLogViewSet
)

router = DefaultRouter()
router.register(r'routers', MikrotikRouterViewSet, basename='mikrotik-router')
router.register(r'hotspot-users', MikrotikHotspotUserViewSet, basename='hotspot-user')
router.register(r'active-connections', MikrotikActiveConnectionViewSet, basename='active-connection')
router.register(r'logs', MikrotikLogViewSet, basename='mikrotik-log')

urlpatterns = [
    path('', include(router.urls)),
]

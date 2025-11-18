from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import (
    RadiusServerViewSet, RadiusAuthLogViewSet,
    RadiusAccountingViewSet, RadiusClientViewSet
)

router = DefaultRouter()
router.register(r'servers', RadiusServerViewSet, basename='radius-server')
router.register(r'auth-logs', RadiusAuthLogViewSet, basename='auth-log')
router.register(r'accounting', RadiusAccountingViewSet, basename='accounting')
router.register(r'clients', RadiusClientViewSet, basename='radius-client')

urlpatterns = [
    path('', include(router.urls)),
]

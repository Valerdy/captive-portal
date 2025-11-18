from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import MikrotikRouter, MikrotikHotspotUser, MikrotikActiveConnection, MikrotikLog
from .serializers import (
    MikrotikRouterSerializer, MikrotikRouterListSerializer,
    MikrotikHotspotUserSerializer, MikrotikActiveConnectionSerializer,
    MikrotikLogSerializer
)


class MikrotikRouterViewSet(viewsets.ModelViewSet):
    """ViewSet for MikrotikRouter model"""
    queryset = MikrotikRouter.objects.all()
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        if self.action == 'list':
            return MikrotikRouterListSerializer
        return MikrotikRouterSerializer

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active routers"""
        routers = MikrotikRouter.objects.filter(is_active=True)
        serializer = MikrotikRouterListSerializer(routers, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test connection to Mikrotik router"""
        router = self.get_object()
        # This would call the Mikrotik Agent API
        # Implementation depends on how you want to integrate with the agent
        return Response({
            'status': 'success',
            'message': f'Connection test for {router.name} - implement actual test'
        })


class MikrotikHotspotUserViewSet(viewsets.ModelViewSet):
    """ViewSet for MikrotikHotspotUser model"""
    queryset = MikrotikHotspotUser.objects.all()
    serializer_class = MikrotikHotspotUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter based on user permissions"""
        user = self.request.user
        if user.is_staff:
            return MikrotikHotspotUser.objects.all()
        return MikrotikHotspotUser.objects.filter(user=user)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active hotspot users"""
        users = self.get_queryset().filter(is_active=True, is_disabled=False)
        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def disable(self, request, pk=None):
        """Disable a hotspot user"""
        hotspot_user = self.get_object()
        hotspot_user.is_disabled = True
        hotspot_user.save()
        return Response({'status': 'user disabled'})

    @action(detail=True, methods=['post'])
    def enable(self, request, pk=None):
        """Enable a hotspot user"""
        hotspot_user = self.get_object()
        hotspot_user.is_disabled = False
        hotspot_user.save()
        return Response({'status': 'user enabled'})


class MikrotikActiveConnectionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for MikrotikActiveConnection model (read-only)"""
    queryset = MikrotikActiveConnection.objects.all()
    serializer_class = MikrotikActiveConnectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter based on user permissions"""
        user = self.request.user
        if user.is_staff:
            return MikrotikActiveConnection.objects.all()
        # Filter by user's hotspot accounts
        return MikrotikActiveConnection.objects.filter(
            hotspot_user__user=user
        )

    @action(detail=True, methods=['post'])
    def disconnect(self, request, pk=None):
        """Disconnect an active session"""
        connection = self.get_object()
        # This would call the Mikrotik Agent API to disconnect
        # Implementation depends on integration with agent
        return Response({
            'status': 'success',
            'message': f'Disconnection requested for {connection.session_id}'
        })


class MikrotikLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for MikrotikLog model (read-only)"""
    queryset = MikrotikLog.objects.all()
    serializer_class = MikrotikLogSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        """Allow filtering by router, level, and operation"""
        queryset = MikrotikLog.objects.all()

        router_id = self.request.query_params.get('router', None)
        if router_id:
            queryset = queryset.filter(router_id=router_id)

        level = self.request.query_params.get('level', None)
        if level:
            queryset = queryset.filter(level=level)

        operation = self.request.query_params.get('operation', None)
        if operation:
            queryset = queryset.filter(operation=operation)

        return queryset

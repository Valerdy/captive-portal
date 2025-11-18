from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import MikrotikRouter, MikrotikHotspotUser, MikrotikActiveConnection, MikrotikLog
from .serializers import (
    MikrotikRouterSerializer, MikrotikRouterListSerializer,
    MikrotikHotspotUserSerializer, MikrotikActiveConnectionSerializer,
    MikrotikLogSerializer
)
from .utils import MikrotikAgentClient
import logging

logger = logging.getLogger(__name__)


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

        try:
            # Create agent client
            client = MikrotikAgentClient()

            # Test connection
            result = client.test_connection()

            # Log the test
            MikrotikLog.objects.create(
                router=router,
                operation='test_connection',
                level='info',
                message=f'Connection test successful for {router.name}',
                details=result
            )

            return Response({
                'status': 'success',
                'message': f'Successfully connected to {router.name}',
                'data': result
            })

        except Exception as e:
            # Log the error
            MikrotikLog.objects.create(
                router=router,
                operation='test_connection',
                level='error',
                message=f'Connection test failed for {router.name}',
                details={'error': str(e)}
            )

            return Response({
                'status': 'error',
                'message': f'Failed to connect to {router.name}',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

        try:
            # Create agent client
            client = MikrotikAgentClient()

            # Disconnect the session
            result = client.disconnect_session(connection.session_id)

            # Log the disconnection
            MikrotikLog.objects.create(
                router=connection.router,
                operation='disconnect_session',
                level='info',
                message=f'Session {connection.session_id} disconnected',
                details=result
            )

            # Update connection status
            connection.delete()  # Remove from active connections

            return Response({
                'status': 'success',
                'message': f'Session {connection.session_id} disconnected successfully',
                'data': result
            })

        except Exception as e:
            # Log the error
            if hasattr(connection, 'router'):
                MikrotikLog.objects.create(
                    router=connection.router,
                    operation='disconnect_session',
                    level='error',
                    message=f'Failed to disconnect session {connection.session_id}',
                    details={'error': str(e)}
                )

            return Response({
                'status': 'error',
                'message': f'Failed to disconnect session',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

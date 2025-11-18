from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import RadiusServer, RadiusAuthLog, RadiusAccounting, RadiusClient
from .serializers import (
    RadiusServerSerializer, RadiusServerListSerializer,
    RadiusAuthLogSerializer, RadiusAccountingSerializer,
    RadiusAccountingListSerializer, RadiusClientSerializer
)


class RadiusServerViewSet(viewsets.ModelViewSet):
    """ViewSet for RadiusServer model"""
    queryset = RadiusServer.objects.all()
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        if self.action == 'list':
            return RadiusServerListSerializer
        return RadiusServerSerializer

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active RADIUS servers"""
        servers = RadiusServer.objects.filter(is_active=True)
        serializer = RadiusServerListSerializer(servers, many=True)
        return Response(serializer.data)


class RadiusAuthLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for RadiusAuthLog model (read-only)"""
    queryset = RadiusAuthLog.objects.all()
    serializer_class = RadiusAuthLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter based on user permissions and query params"""
        user = self.request.user
        queryset = RadiusAuthLog.objects.all()

        if not user.is_staff:
            queryset = queryset.filter(user=user)

        # Filter by username
        username = self.request.query_params.get('username', None)
        if username:
            queryset = queryset.filter(username=username)

        # Filter by status
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)

        # Filter by server
        server_id = self.request.query_params.get('server', None)
        if server_id:
            queryset = queryset.filter(server_id=server_id)

        return queryset

    @action(detail=False, methods=['get'])
    def failed(self, request):
        """Get all failed authentication attempts"""
        logs = self.get_queryset().filter(status='reject')
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)


class RadiusAccountingViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for RadiusAccounting model (read-only)"""
    queryset = RadiusAccounting.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return RadiusAccountingListSerializer
        return RadiusAccountingSerializer

    def get_queryset(self):
        """Filter based on user permissions and query params"""
        user = self.request.user
        queryset = RadiusAccounting.objects.all()

        if not user.is_staff:
            queryset = queryset.filter(user=user)

        # Filter by username
        username = self.request.query_params.get('username', None)
        if username:
            queryset = queryset.filter(username=username)

        # Filter by status type
        status_type = self.request.query_params.get('status_type', None)
        if status_type:
            queryset = queryset.filter(status_type=status_type)

        # Filter by session ID
        session_id = self.request.query_params.get('session_id', None)
        if session_id:
            queryset = queryset.filter(session_id=session_id)

        return queryset

    @action(detail=False, methods=['get'])
    def active_sessions(self, request):
        """Get all active sessions (start without stop)"""
        sessions = self.get_queryset().filter(status_type='start')
        # Filter out sessions that have a corresponding stop record
        active_sessions = []
        for session in sessions:
            has_stop = RadiusAccounting.objects.filter(
                session_id=session.session_id,
                status_type='stop'
            ).exists()
            if not has_stop:
                active_sessions.append(session)

        serializer = self.get_serializer(active_sessions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get accounting statistics"""
        queryset = self.get_queryset()

        total_sessions = queryset.filter(status_type='stop').count()
        total_data = sum(r.total_octets for r in queryset.filter(status_type='stop'))

        stats = {
            'total_sessions': total_sessions,
            'total_data_bytes': total_data,
            'active_sessions': queryset.filter(status_type='start').count()
        }
        return Response(stats)


class RadiusClientViewSet(viewsets.ModelViewSet):
    """ViewSet for RadiusClient model"""
    queryset = RadiusClient.objects.all()
    serializer_class = RadiusClientSerializer
    permission_classes = [permissions.IsAdminUser]

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active RADIUS clients"""
        clients = RadiusClient.objects.filter(is_active=True)
        serializer = self.get_serializer(clients, many=True)
        return Response(serializer.data)

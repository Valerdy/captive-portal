from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import (
    RadiusServer, RadiusAuthLog, RadiusAccounting, RadiusClient,
    RadCheck, RadReply, RadUserGroup, RadGroupCheck, RadGroupReply, RadPostAuth
)
from .serializers import (
    RadiusServerSerializer, RadiusServerListSerializer,
    RadiusAuthLogSerializer, RadiusAccountingSerializer,
    RadiusAccountingListSerializer, RadiusClientSerializer,
    RadCheckSerializer, RadReplySerializer, RadUserGroupSerializer,
    RadGroupCheckSerializer, RadGroupReplySerializer, RadPostAuthSerializer,
    RadiusUserSerializer
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


# ============================================================================
# FreeRADIUS User Management ViewSets
# ============================================================================

class RadiusUserViewSet(viewsets.ViewSet):
    """
    ViewSet for managing complete RADIUS users
    Provides CRUD operations that handle radcheck, radreply, and radusergroup tables
    """
    permission_classes = [permissions.IsAdminUser]

    def list(self, request):
        """List all RADIUS users"""
        # Get unique usernames from radcheck
        usernames = RadCheck.objects.values_list('username', flat=True).distinct()

        users_data = []
        for username in usernames:
            # Get user data from various tables
            check = RadCheck.objects.filter(username=username, attribute='Cleartext-Password').first()
            timeout_reply = RadReply.objects.filter(username=username, attribute='Session-Timeout').first()
            bandwidth_reply = RadReply.objects.filter(username=username, attribute='Mikrotik-Rate-Limit').first()
            group = RadUserGroup.objects.filter(username=username).first()

            user_data = {
                'username': username,
                'groupname': group.groupname if group else 'user',
                'session_timeout': int(timeout_reply.value) if timeout_reply else 3600,
                'bandwidth_limit': bandwidth_reply.value if bandwidth_reply else ''
            }
            users_data.append(user_data)

        return Response(users_data)

    def create(self, request):
        """Create a new RADIUS user"""
        serializer = RadiusUserSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        """Get a specific RADIUS user by username"""
        username = pk

        # Check if user exists
        if not RadCheck.objects.filter(username=username).exists():
            return Response(
                {'error': f'User {username} not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get user data
        check = RadCheck.objects.filter(username=username, attribute='Cleartext-Password').first()
        timeout_reply = RadReply.objects.filter(username=username, attribute='Session-Timeout').first()
        bandwidth_reply = RadReply.objects.filter(username=username, attribute='Mikrotik-Rate-Limit').first()
        group = RadUserGroup.objects.filter(username=username).first()

        user_data = {
            'username': username,
            'groupname': group.groupname if group else 'user',
            'session_timeout': int(timeout_reply.value) if timeout_reply else 3600,
            'bandwidth_limit': bandwidth_reply.value if bandwidth_reply else ''
        }

        return Response(user_data)

    def update(self, request, pk=None):
        """Update a RADIUS user"""
        username = pk

        if not RadCheck.objects.filter(username=username).exists():
            return Response(
                {'error': f'User {username} not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get existing data
        existing_data = {'username': username}

        serializer = RadiusUserSerializer(instance=existing_data, data=request.data, partial=True)
        if serializer.is_valid():
            with transaction.atomic():
                serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        """Partially update a RADIUS user"""
        return self.update(request, pk)

    def destroy(self, request, pk=None):
        """Delete a RADIUS user"""
        username = pk

        if not RadCheck.objects.filter(username=username).exists():
            return Response(
                {'error': f'User {username} not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        with transaction.atomic():
            # Delete from all related tables
            RadCheck.objects.filter(username=username).delete()
            RadReply.objects.filter(username=username).delete()
            RadUserGroup.objects.filter(username=username).delete()

        return Response({'message': f'User {username} deleted'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def by_group(self, request):
        """Get all users in a specific group"""
        groupname = request.query_params.get('groupname', 'user')
        usernames = RadUserGroup.objects.filter(groupname=groupname).values_list('username', flat=True)

        users_data = []
        for username in usernames:
            check = RadCheck.objects.filter(username=username, attribute='Cleartext-Password').first()
            timeout_reply = RadReply.objects.filter(username=username, attribute='Session-Timeout').first()

            user_data = {
                'username': username,
                'groupname': groupname,
                'session_timeout': int(timeout_reply.value) if timeout_reply else 3600
            }
            users_data.append(user_data)

        return Response(users_data)


class RadCheckViewSet(viewsets.ModelViewSet):
    """ViewSet for RadCheck model (direct access)"""
    queryset = RadCheck.objects.all()
    serializer_class = RadCheckSerializer
    permission_classes = [permissions.IsAdminUser]


class RadReplyViewSet(viewsets.ModelViewSet):
    """ViewSet for RadReply model (direct access)"""
    queryset = RadReply.objects.all()
    serializer_class = RadReplySerializer
    permission_classes = [permissions.IsAdminUser]


class RadUserGroupViewSet(viewsets.ModelViewSet):
    """ViewSet for RadUserGroup model (direct access)"""
    queryset = RadUserGroup.objects.all()
    serializer_class = RadUserGroupSerializer
    permission_classes = [permissions.IsAdminUser]


class RadGroupCheckViewSet(viewsets.ModelViewSet):
    """ViewSet for RadGroupCheck model"""
    queryset = RadGroupCheck.objects.all()
    serializer_class = RadGroupCheckSerializer
    permission_classes = [permissions.IsAdminUser]


class RadGroupReplyViewSet(viewsets.ModelViewSet):
    """ViewSet for RadGroupReply model"""
    queryset = RadGroupReply.objects.all()
    serializer_class = RadGroupReplySerializer
    permission_classes = [permissions.IsAdminUser]


class RadPostAuthViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for RadPostAuth model (read-only authentication logs)"""
    queryset = RadPostAuth.objects.all()
    serializer_class = RadPostAuthSerializer
    permission_classes = [permissions.IsAdminUser]

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent authentication attempts"""
        limit = int(request.query_params.get('limit', 100))
        logs = RadPostAuth.objects.all()[:limit]
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_username(self, request):
        """Get authentication logs for a specific username"""
        username = request.query_params.get('username')
        if not username:
            return Response({'error': 'username parameter required'}, status=status.HTTP_400_BAD_REQUEST)

        logs = RadPostAuth.objects.filter(username=username)
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import User, Device, Session, Voucher
from .serializers import (
    UserSerializer, UserListSerializer, DeviceSerializer,
    SessionSerializer, SessionListSerializer, VoucherSerializer,
    VoucherValidationSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User model"""
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user information"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def devices(self, request, pk=None):
        """Get all devices for a user"""
        user = self.get_object()
        devices = user.devices.all()
        serializer = DeviceSerializer(devices, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def sessions(self, request, pk=None):
        """Get all sessions for a user"""
        user = self.get_object()
        sessions = user.sessions.all()
        serializer = SessionListSerializer(sessions, many=True)
        return Response(serializer.data)


class DeviceViewSet(viewsets.ModelViewSet):
    """ViewSet for Device model"""
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter devices based on user permissions"""
        user = self.request.user
        if user.is_staff:
            return Device.objects.all()
        return Device.objects.filter(user=user)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active devices"""
        devices = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(devices, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a device"""
        device = self.get_object()
        device.is_active = False
        device.save()
        return Response({'status': 'device deactivated'})


class SessionViewSet(viewsets.ModelViewSet):
    """ViewSet for Session model"""
    queryset = Session.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return SessionListSerializer
        return SessionSerializer

    def get_queryset(self):
        """Filter sessions based on user permissions"""
        user = self.request.user
        if user.is_staff:
            return Session.objects.all()
        return Session.objects.filter(user=user)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active sessions"""
        sessions = self.get_queryset().filter(status='active')
        serializer = self.get_serializer(sessions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        """Terminate a session"""
        session = self.get_object()
        session.status = 'terminated'
        session.end_time = timezone.now()
        session.save()
        return Response({'status': 'session terminated'})

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get session statistics for current user"""
        user = request.user
        sessions = Session.objects.filter(user=user)

        stats = {
            'total_sessions': sessions.count(),
            'active_sessions': sessions.filter(status='active').count(),
            'total_data_transferred': sum(s.total_bytes for s in sessions),
            'average_session_duration': sessions.filter(
                end_time__isnull=False
            ).aggregate(
                avg_duration=timezone.now() - timezone.now()
            )
        }
        return Response(stats)


class VoucherViewSet(viewsets.ModelViewSet):
    """ViewSet for Voucher model"""
    queryset = Voucher.objects.all()
    serializer_class = VoucherSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['validate', 'redeem']:
            return [permissions.AllowAny()]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Set created_by to current user"""
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['post'])
    def validate(self, request):
        """Validate a voucher code"""
        serializer = VoucherValidationSerializer(data=request.data)
        if serializer.is_valid():
            code = serializer.validated_data['code']
            voucher = Voucher.objects.get(code=code)
            voucher_serializer = VoucherSerializer(voucher)
            return Response({
                'valid': True,
                'voucher': voucher_serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def redeem(self, request):
        """Redeem a voucher code"""
        serializer = VoucherValidationSerializer(data=request.data)
        if serializer.is_valid():
            code = serializer.validated_data['code']
            voucher = Voucher.objects.get(code=code)

            # Check if user is authenticated
            if request.user.is_authenticated:
                voucher.used_by = request.user
                voucher.used_at = timezone.now()
                voucher.used_count += 1

                # Update voucher status if max devices reached
                if voucher.used_count >= voucher.max_devices:
                    voucher.status = 'used'

                voucher.save()

                return Response({
                    'status': 'success',
                    'message': 'Voucher redeemed successfully',
                    'duration': voucher.duration
                })
            else:
                return Response(
                    {'error': 'Authentication required to redeem voucher'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active vouchers"""
        vouchers = Voucher.objects.filter(status='active')
        serializer = self.get_serializer(vouchers, many=True)
        return Response(serializer.data)

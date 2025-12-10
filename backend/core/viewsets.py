from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import User, Device, Session, Voucher, BlockedSite, UserQuota, Promotion
from .serializers import (
    UserSerializer, UserListSerializer, DeviceSerializer,
    SessionSerializer, SessionListSerializer, VoucherSerializer,
    VoucherValidationSerializer, BlockedSiteSerializer, UserQuotaSerializer,
    PromotionSerializer
)
from .permissions import IsAdmin, IsAdminOrReadOnly, IsOwnerOrAdmin, IsAuthenticatedUser
from .decorators import rate_limit
from radius.models import RadCheck


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User model"""
    queryset = User.objects.all()
    permission_classes = [IsAuthenticatedUser]

    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        return UserSerializer

    def get_permissions(self):
        """
        Permissions:
        - create: AllowAny (for registration)
        - list: Admin only
        - retrieve/update/destroy: Admin or owner
        """
        if self.action == 'create':
            return [permissions.AllowAny()]
        elif self.action == 'list':
            return [IsAdmin()]
        elif self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return [IsOwnerOrAdmin()]
        return super().get_permissions()

    def get_queryset(self):
        """Filter users based on role"""
        user = self.request.user
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            # Admins see all users
            return User.objects.all()
        elif user.is_authenticated:
            # Regular users see only themselves
            return User.objects.filter(id=user.id)
        return User.objects.none()

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

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def deactivate_radius(self, request, pk=None):
        """Désactive l'utilisateur dans FreeRADIUS (statut=0)"""
        user = self.get_object()
        from radius.models import RadCheck

        updated = RadCheck.objects.filter(username=user.username).update(statut=False)
        return Response({
            'status': 'disabled',
            'updated': updated
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def activate_radius(self, request, pk=None):
        """Active l'utilisateur dans FreeRADIUS (statut=1)"""
        user = self.get_object()
        from radius.models import RadCheck

        if not user.cleartext_password:
            return Response({'error': 'Mot de passe en clair indisponible pour cet utilisateur'}, status=status.HTTP_400_BAD_REQUEST)

        RadCheck.objects.update_or_create(
            username=user.username,
            attribute='Cleartext-Password',
            defaults={
                'op': ':=',
                'value': user.cleartext_password,
                'statut': True
            }
        )
        return Response({'status': 'enabled'})


class DeviceViewSet(viewsets.ModelViewSet):
    """ViewSet for Device model"""
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticatedUser]

    def get_permissions(self):
        """
        Permissions:
        - list/retrieve: Owner or admin
        - create/update/delete: Owner or admin
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsOwnerOrAdmin()]
        return super().get_permissions()

    def get_queryset(self):
        """Filter devices based on user role"""
        user = self.request.user
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            # Admins see all devices
            return Device.objects.all()
        elif user.is_authenticated:
            # Regular users see only their devices
            return Device.objects.filter(user=user)
        return Device.objects.none()

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
    permission_classes = [IsAuthenticatedUser]

    def get_serializer_class(self):
        if self.action == 'list':
            return SessionListSerializer
        return SessionSerializer

    def get_permissions(self):
        """
        Permissions:
        - list/retrieve: Owner or admin
        - terminate: Owner or admin
        - statistics: Owner or admin
        """
        if self.action in ['terminate', 'statistics']:
            return [IsAuthenticatedUser()]
        return super().get_permissions()

    def get_queryset(self):
        """Filter sessions based on user role"""
        user = self.request.user
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            # Admins see all sessions
            return Session.objects.all()
        elif user.is_authenticated:
            # Regular users see only their sessions
            return Session.objects.filter(user=user)
        return Session.objects.none()

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

        # Calculate average session duration
        completed_sessions = sessions.filter(end_time__isnull=False)
        total_duration = 0
        session_count = 0

        for session in completed_sessions:
            if session.start_time and session.end_time:
                duration = (session.end_time - session.start_time).total_seconds()
                total_duration += duration
                session_count += 1

        avg_duration = total_duration / session_count if session_count > 0 else 0

        stats = {
            'total_sessions': sessions.count(),
            'active_sessions': sessions.filter(status='active').count(),
            'total_data_transferred': sum(s.total_bytes for s in sessions),
            'average_session_duration_seconds': avg_duration,
            'average_session_duration_minutes': round(avg_duration / 60, 2) if avg_duration > 0 else 0
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
    @rate_limit(key_prefix='voucher_validate', rate='10/m', method='POST', block_duration=120)
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
    @rate_limit(key_prefix='voucher_redeem', rate='5/h', method='POST', block_duration=300)
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


class BlockedSiteViewSet(viewsets.ModelViewSet):
    """ViewSet for BlockedSite model"""
    queryset = BlockedSite.objects.all()
    serializer_class = BlockedSiteSerializer
    permission_classes = [IsAdmin]

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active blocked sites"""
        sites = BlockedSite.objects.filter(is_active=True)
        serializer = self.get_serializer(sites, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def blacklist(self, request):
        """Get all blacklisted sites"""
        sites = BlockedSite.objects.filter(type='blacklist', is_active=True)
        serializer = self.get_serializer(sites, many=True)
        return Response(serializer.data)


class PromotionViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les promotions (activation/désactivation en masse)"""
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer
    permission_classes = [IsAdmin]

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def active(self, request):
        """Liste des promotions actives (accessible publiquement pour l'inscription)"""
        active_promotions = Promotion.objects.filter(is_active=True)
        serializer = self.get_serializer(active_promotions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Désactive une promotion et désactive l'accès WiFi de tous ses utilisateurs.
        Utilise une transaction atomique pour garantir la cohérence.
        """
        from django.db import transaction

        promotion = self.get_object()

        try:
            with transaction.atomic():
                # Désactiver la promotion
                promotion.is_active = False
                promotion.save(update_fields=['is_active'])

                # Récupérer tous les utilisateurs qui ont été provisionnés dans RADIUS
                users_to_disable = promotion.users.filter(is_radius_activated=True)
                disabled_count = 0
                failed_count = 0
                errors = []

                for user in users_to_disable:
                    try:
                        # Utiliser select_for_update pour éviter les race conditions
                        user = User.objects.select_for_update().get(id=user.id)

                        # Désactiver dans radcheck
                        updated = RadCheck.objects.filter(username=user.username).update(statut=False)

                        if updated > 0:
                            # Mettre à jour le statut dans User
                            user.is_radius_enabled = False
                            user.save(update_fields=['is_radius_enabled'])
                            disabled_count += 1
                        else:
                            failed_count += 1
                            errors.append(f"{user.username}: Non trouvé dans radcheck")
                    except Exception as e:
                        failed_count += 1
                        errors.append(f"{user.username}: {str(e)}")

                return Response({
                    'status': 'success',
                    'promotion': promotion.name,
                    'is_active': promotion.is_active,
                    'users_disabled': disabled_count,
                    'users_failed': failed_count,
                    'errors': errors if errors else None,
                    'message': f'Promotion désactivée. {disabled_count} utilisateur(s) désactivé(s) dans RADIUS.'
                })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Erreur lors de la désactivation: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Active une promotion et réactive l'accès WiFi de tous ses utilisateurs déjà provisionnés.
        Utilise une transaction atomique pour garantir la cohérence.
        """
        from django.db import transaction

        promotion = self.get_object()

        try:
            with transaction.atomic():
                # Activer la promotion
                promotion.is_active = True
                promotion.save(update_fields=['is_active'])

                # Réactiver uniquement les utilisateurs déjà provisionnés dans RADIUS
                users_to_enable = promotion.users.filter(is_radius_activated=True)
                enabled_count = 0
                failed_count = 0
                errors = []

                for user in users_to_enable:
                    try:
                        # Utiliser select_for_update pour éviter les race conditions
                        user = User.objects.select_for_update().get(id=user.id)

                        # Réactiver dans radcheck
                        updated = RadCheck.objects.filter(username=user.username).update(statut=True)

                        if updated > 0:
                            # Mettre à jour le statut dans User
                            user.is_radius_enabled = True
                            user.save(update_fields=['is_radius_enabled'])
                            enabled_count += 1
                        else:
                            failed_count += 1
                            errors.append(f"{user.username}: Non trouvé dans radcheck")
                    except Exception as e:
                        failed_count += 1
                        errors.append(f"{user.username}: {str(e)}")

                return Response({
                    'status': 'success',
                    'promotion': promotion.name,
                    'is_active': promotion.is_active,
                    'users_enabled': enabled_count,
                    'users_failed': failed_count,
                    'errors': errors if errors else None,
                    'message': f'Promotion activée. {enabled_count} utilisateur(s) réactivé(s) dans RADIUS.'
                })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Erreur lors de l\'activation: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserQuotaViewSet(viewsets.ModelViewSet):
    """ViewSet for UserQuota model"""
    queryset = UserQuota.objects.all()
    serializer_class = UserQuotaSerializer
    permission_classes = [IsAdmin]

    @action(detail=True, methods=['post'])
    def reset_daily(self, request, pk=None):
        """Reset daily usage for a user quota"""
        quota = self.get_object()
        quota.reset_daily()
        serializer = self.get_serializer(quota)
        return Response({
            'status': 'success',
            'message': 'Daily usage reset successfully',
            'quota': serializer.data
        })

    @action(detail=True, methods=['post'])
    def reset_weekly(self, request, pk=None):
        """Reset weekly usage for a user quota"""
        quota = self.get_object()
        quota.reset_weekly()
        serializer = self.get_serializer(quota)
        return Response({
            'status': 'success',
            'message': 'Weekly usage reset successfully',
            'quota': serializer.data
        })

    @action(detail=True, methods=['post'])
    def reset_monthly(self, request, pk=None):
        """Reset monthly usage for a user quota"""
        quota = self.get_object()
        quota.reset_monthly()
        serializer = self.get_serializer(quota)
        return Response({
            'status': 'success',
            'message': 'Monthly usage reset successfully',
            'quota': serializer.data
        })

    @action(detail=True, methods=['post'])
    def reset_all(self, request, pk=None):
        """Reset all usage counters for a user quota"""
        quota = self.get_object()
        quota.reset_all()
        serializer = self.get_serializer(quota)
        return Response({
            'status': 'success',
            'message': 'All usage counters reset successfully',
            'quota': serializer.data
        })

    @action(detail=False, methods=['get'])
    def exceeded(self, request):
        """Get all quotas that are exceeded"""
        quotas = UserQuota.objects.filter(is_exceeded=True)
        serializer = self.get_serializer(quotas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def create_for_user(self, request):
        """Create a quota for a specific user"""
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if quota already exists
        if hasattr(user, 'quota'):
            return Response(
                {'error': 'Quota already exists for this user'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create quota with optional custom limits
        quota_data = {
            'user': user,
            'daily_limit': request.data.get('daily_limit', 5368709120),  # 5GB
            'weekly_limit': request.data.get('weekly_limit', 32212254720),  # 30GB
            'monthly_limit': request.data.get('monthly_limit', 128849018880),  # 120GB
        }
        quota = UserQuota.objects.create(**quota_data)
        serializer = self.get_serializer(quota)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

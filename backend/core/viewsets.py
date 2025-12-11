from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import User, Device, Session, Voucher, BlockedSite, UserQuota, Promotion, Profile
from .serializers import (
    UserSerializer, UserListSerializer, DeviceSerializer,
    SessionSerializer, SessionListSerializer, VoucherSerializer,
    VoucherValidationSerializer, BlockedSiteSerializer, UserQuotaSerializer,
    PromotionSerializer, ProfileSerializer
)
from .permissions import IsAdmin, IsAdminOrReadOnly, IsOwnerOrAdmin, IsAuthenticatedUser
from .decorators import rate_limit
from radius.models import RadCheck


class ProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for Profile model"""
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        """Filtre les profils actifs pour les non-admins"""
        user = self.request.user
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            # Admins see all profiles
            return Profile.objects.all()
        # Regular users see only active profiles
        return Profile.objects.filter(is_active=True)

    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """Récupère la liste des utilisateurs utilisant ce profil"""
        profile = self.get_object()
        users = profile.users.filter(is_active=True)

        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'promotion': {'id': user.promotion.id, 'name': user.promotion.name} if user.promotion else None,
                'is_active': user.is_active,
                'is_radius_activated': user.is_radius_activated,
            })

        return Response({
            'profile': {'id': profile.id, 'name': profile.name},
            'users': users_data,
            'total_count': len(users_data)
        })

    @action(detail=True, methods=['get'])
    def promotions(self, request, pk=None):
        """Récupère la liste des promotions utilisant ce profil"""
        profile = self.get_object()
        promotions = profile.promotions.filter(is_active=True)

        promotions_data = []
        for promotion in promotions:
            promotions_data.append({
                'id': promotion.id,
                'name': promotion.name,
                'is_active': promotion.is_active,
                'user_count': promotion.users.count()
            })

        return Response({
            'profile': {'id': profile.id, 'name': profile.name},
            'promotions': promotions_data,
            'total_count': len(promotions_data)
        })

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Liste des profils actifs uniquement"""
        active_profiles = Profile.objects.filter(is_active=True)
        serializer = self.get_serializer(active_profiles, many=True)
        return Response(serializer.data)


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
        """Active l'utilisateur dans FreeRADIUS avec les paramètres de son profil"""
        user = self.get_object()
        from radius.models import RadCheck, RadReply, RadUserGroup

        if not user.cleartext_password:
            return Response({
                'error': 'Mot de passe en clair indisponible pour cet utilisateur'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Récupérer le profil effectif (individuel ou de promotion)
        profile = user.get_effective_profile()

        # 1. radcheck - Mot de passe en clair
        RadCheck.objects.update_or_create(
            username=user.username,
            attribute='Cleartext-Password',
            defaults={
                'op': ':=',
                'value': user.cleartext_password,
                'statut': True
            }
        )

        # 2. radreply - Session timeout (du profil ou valeur par défaut)
        session_timeout = profile.session_timeout if profile else (86400 if user.is_staff else 3600)
        RadReply.objects.update_or_create(
            username=user.username,
            attribute='Session-Timeout',
            defaults={'op': '=', 'value': str(session_timeout)}
        )

        # 3. radreply - Idle timeout (du profil)
        if profile:
            RadReply.objects.update_or_create(
                username=user.username,
                attribute='Idle-Timeout',
                defaults={'op': '=', 'value': str(profile.idle_timeout)}
            )

        # 4. radreply - Limite de bande passante (du profil ou valeur par défaut)
        if profile:
            upload_mbps = profile.bandwidth_upload / 1024
            download_mbps = profile.bandwidth_download / 1024
            bandwidth_value = f"{int(upload_mbps)}M/{int(download_mbps)}M"
        else:
            bandwidth_value = '10M/10M'

        RadReply.objects.update_or_create(
            username=user.username,
            attribute='Mikrotik-Rate-Limit',
            defaults={'op': '=', 'value': bandwidth_value}
        )

        # 5. radcheck - Simultaneous-Use (du profil ou valeur par défaut)
        simultaneous_use = profile.simultaneous_use if profile else 1
        RadCheck.objects.update_or_create(
            username=user.username,
            attribute='Simultaneous-Use',
            defaults={'op': ':=', 'value': str(simultaneous_use), 'statut': True}
        )

        # 6. radcheck - Quota de données (si le profil a un quota limité)
        if profile and profile.quota_type == 'limited':
            RadCheck.objects.update_or_create(
                username=user.username,
                attribute='ChilliSpot-Max-Total-Octets',
                defaults={'op': ':=', 'value': str(profile.data_volume), 'statut': True}
            )

        # 7. radusergroup - Groupe utilisateur
        RadUserGroup.objects.update_or_create(
            username=user.username,
            groupname=user.role,
            defaults={'priority': 0}
        )

        # Mettre à jour les statuts
        user.is_radius_activated = True
        user.is_radius_enabled = True
        user.save(update_fields=['is_radius_activated', 'is_radius_enabled'])

        return Response({
            'status': 'enabled',
            'profile': profile.name if profile else 'Default',
            'bandwidth': bandwidth_value,
            'session_timeout': session_timeout,
            'quota_type': profile.quota_type if profile else 'unlimited'
        })


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

    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """Récupère la liste des utilisateurs d'une promotion avec leurs statuts RADIUS"""
        promotion = self.get_object()
        users = promotion.users.filter(is_active=True).select_related('promotion')

        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'matricule': user.matricule,
                'is_active': user.is_active,
                'is_radius_activated': user.is_radius_activated,
                'is_radius_enabled': user.is_radius_enabled,
                'radius_status': user.get_radius_status_display(),
                'can_access_radius': user.can_access_radius(),
            })

        return Response({
            'promotion': {
                'id': promotion.id,
                'code': promotion.code,
                'name': promotion.name,
                'is_active': promotion.is_active
            },
            'users': users_data,
            'total_count': len(users_data)
        })

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Désactive une promotion et SUPPRIME tous les utilisateurs de RADIUS.
        Les utilisateurs n'auront plus accès à Internet.
        Utilise une transaction atomique pour garantir la cohérence.
        """
        from django.db import transaction
        from radius.models import RadReply, RadUserGroup

        promotion = self.get_object()

        try:
            with transaction.atomic():
                # Désactiver la promotion
                promotion.is_active = False
                promotion.save(update_fields=['is_active'])

                # Récupérer TOUS les utilisateurs actifs de la promotion
                users_to_disable = promotion.users.filter(is_active=True)
                disabled_count = 0
                failed_count = 0
                errors = []

                for user in users_to_disable:
                    try:
                        # Utiliser select_for_update pour éviter les race conditions
                        user = User.objects.select_for_update().get(id=user.id)

                        # SUPPRIMER toutes les entrées RADIUS
                        RadCheck.objects.filter(username=user.username).delete()
                        RadReply.objects.filter(username=user.username).delete()
                        RadUserGroup.objects.filter(username=user.username).delete()

                        # Mettre à jour les statuts dans User
                        user.is_radius_activated = False
                        user.is_radius_enabled = False
                        user.save(update_fields=['is_radius_activated', 'is_radius_enabled'])

                        disabled_count += 1

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
                    'message': f'Promotion désactivée. {disabled_count} utilisateur(s) supprimé(s) de RADIUS.'
                })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Erreur lors de la désactivation: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Active une promotion et CRÉE les entrées RADIUS pour TOUS les utilisateurs.
        Tous les utilisateurs auront accès à Internet.
        Utilise une transaction atomique pour garantir la cohérence.
        """
        from django.db import transaction
        from radius.models import RadReply, RadUserGroup

        promotion = self.get_object()

        try:
            with transaction.atomic():
                # Activer la promotion
                promotion.is_active = True
                promotion.save(update_fields=['is_active'])

                # Récupérer TOUS les utilisateurs actifs de la promotion
                users_to_enable = promotion.users.filter(is_active=True)
                enabled_count = 0
                failed_count = 0
                errors = []

                for user in users_to_enable:
                    try:
                        # Utiliser select_for_update pour éviter les race conditions
                        user = User.objects.select_for_update().get(id=user.id)

                        # Vérifier que le mot de passe en clair est disponible
                        if not user.cleartext_password:
                            failed_count += 1
                            errors.append(f"{user.username}: Mot de passe en clair non disponible")
                            continue

                        # CRÉER les entrées RADIUS avec les paramètres du profil

                        # Récupérer le profil effectif (individuel ou de promotion)
                        profile = user.get_effective_profile()

                        # 1. radcheck - Mot de passe en clair
                        RadCheck.objects.update_or_create(
                            username=user.username,
                            attribute='Cleartext-Password',
                            defaults={
                                'op': ':=',
                                'value': user.cleartext_password,
                                'statut': True
                            }
                        )

                        # 2. radreply - Session timeout (du profil ou valeur par défaut)
                        session_timeout = profile.session_timeout if profile else (86400 if user.is_staff else 3600)
                        RadReply.objects.update_or_create(
                            username=user.username,
                            attribute='Session-Timeout',
                            defaults={
                                'op': '=',
                                'value': str(session_timeout)
                            }
                        )

                        # 3. radreply - Idle timeout (du profil ou valeur par défaut)
                        if profile:
                            RadReply.objects.update_or_create(
                                username=user.username,
                                attribute='Idle-Timeout',
                                defaults={
                                    'op': '=',
                                    'value': str(profile.idle_timeout)
                                }
                            )

                        # 4. radreply - Limite de bande passante (du profil ou valeur par défaut)
                        if profile:
                            # Format Mikrotik: upload/download en bps
                            # Profil stocke en Kbps, Mikrotik attend en bps ou format "5M/10M"
                            upload_mbps = profile.bandwidth_upload / 1024  # Convertir Kbps en Mbps
                            download_mbps = profile.bandwidth_download / 1024
                            bandwidth_value = f"{int(upload_mbps)}M/{int(download_mbps)}M"
                        else:
                            bandwidth_value = '10M/10M'  # Valeur par défaut

                        RadReply.objects.update_or_create(
                            username=user.username,
                            attribute='Mikrotik-Rate-Limit',
                            defaults={
                                'op': '=',
                                'value': bandwidth_value
                            }
                        )

                        # 5. radcheck - Simultaneous-Use (du profil ou valeur par défaut)
                        simultaneous_use = profile.simultaneous_use if profile else 1
                        RadCheck.objects.update_or_create(
                            username=user.username,
                            attribute='Simultaneous-Use',
                            defaults={
                                'op': ':=',
                                'value': str(simultaneous_use),
                                'statut': True
                            }
                        )

                        # 6. radcheck - Quota de données (si le profil a un quota limité)
                        if profile and profile.quota_type == 'limited':
                            # ChilliSpot-Max-Total-Octets pour quota total
                            RadCheck.objects.update_or_create(
                                username=user.username,
                                attribute='ChilliSpot-Max-Total-Octets',
                                defaults={
                                    'op': ':=',
                                    'value': str(profile.data_volume),
                                    'statut': True
                                }
                            )

                        # 7. radusergroup - Groupe utilisateur
                        RadUserGroup.objects.update_or_create(
                            username=user.username,
                            groupname=user.role,
                            defaults={'priority': 0}
                        )

                        # Mettre à jour les statuts dans User
                        user.is_radius_activated = True
                        user.is_radius_enabled = True
                        user.save(update_fields=['is_radius_activated', 'is_radius_enabled'])

                        enabled_count += 1

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
                    'message': f'Promotion activée. {enabled_count} utilisateur(s) créé(s) dans RADIUS.'
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

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import APIException, NotFound, ValidationError as DRFValidationError
from django.utils import timezone
from django.db import models, transaction
from django.core.exceptions import ObjectDoesNotExist
from .models import (
    User, Device, Session, Voucher, BlockedSite, UserQuota, Promotion, Profile,
    UserProfileUsage, ProfileHistory, ProfileAlert, UserDisconnectionLog
)
from .serializers import (
    UserSerializer, UserListSerializer, DeviceSerializer,
    SessionSerializer, SessionListSerializer, VoucherSerializer,
    VoucherValidationSerializer, BlockedSiteSerializer, UserQuotaSerializer,
    PromotionSerializer, ProfileSerializer,
    UserProfileUsageSerializer, ProfileHistorySerializer, ProfileAlertSerializer,
    UserDisconnectionLogSerializer
)
from .permissions import IsAdmin, IsAdminOrReadOnly, IsOwnerOrAdmin, IsAuthenticatedUser
from .decorators import rate_limit
from radius.models import RadCheck


# =============================================================================
# PAGINATION CLASSES
# =============================================================================

class StandardResultsSetPagination(PageNumberPagination):
    """Pagination standard pour les listes d'objets"""
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class LargeResultsSetPagination(PageNumberPagination):
    """Pagination pour les grandes listes (users, statistics)"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


# =============================================================================
# CUSTOM API EXCEPTIONS
# =============================================================================

class ResourceNotFoundError(APIException):
    """Exception pour ressource non trouvée"""
    status_code = 404
    default_detail = 'La ressource demandée n\'existe pas.'
    default_code = 'not_found'


class ResourceAlreadyExistsError(APIException):
    """Exception pour ressource déjà existante"""
    status_code = 409
    default_detail = 'Cette ressource existe déjà.'
    default_code = 'already_exists'


class RadiusActivationError(APIException):
    """Exception pour erreurs d'activation RADIUS"""
    status_code = 400
    default_detail = 'Erreur lors de l\'activation RADIUS.'
    default_code = 'radius_activation_error'


class VoucherValidationError(APIException):
    """Exception pour erreurs de validation de voucher"""
    status_code = 400
    default_detail = 'Le voucher est invalide.'
    default_code = 'voucher_validation_error'


class VoucherNotFoundError(APIException):
    """Exception pour voucher non trouvé"""
    status_code = 404
    default_detail = 'Le code voucher n\'existe pas.'
    default_code = 'voucher_not_found'


class VoucherExpiredError(APIException):
    """Exception pour voucher expiré"""
    status_code = 410
    default_detail = 'Ce voucher a expiré.'
    default_code = 'voucher_expired'


class VoucherAlreadyUsedError(APIException):
    """Exception pour voucher déjà utilisé"""
    status_code = 409
    default_detail = 'Ce voucher a déjà été utilisé.'
    default_code = 'voucher_already_used'


class OperationNotAllowedError(APIException):
    """Exception pour opération non autorisée"""
    status_code = 403
    default_detail = 'Cette opération n\'est pas autorisée.'
    default_code = 'operation_not_allowed'


class RaceConditionError(APIException):
    """Exception pour race condition détectée"""
    status_code = 409
    default_detail = 'Une opération concurrente a été détectée. Veuillez réessayer.'
    default_code = 'race_condition'


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def format_api_error(code: str, message: str, details: dict = None) -> dict:
    """Formate une réponse d'erreur API standardisée"""
    response = {
        'error': {
            'code': code,
            'message': message
        }
    }
    if details:
        response['error']['details'] = details
    return response


def format_api_success(message: str, data: dict = None) -> dict:
    """Formate une réponse de succès API standardisée"""
    response = {
        'success': True,
        'message': message
    }
    if data:
        response['data'] = data
    return response


class ProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for Profile model"""
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Filtre les profils actifs pour les non-admins"""
        user = self.request.user
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            # Admins see all profiles
            return Profile.objects.all()
        # Regular users see only active profiles
        return Profile.objects.filter(is_active=True)

    @action(detail=True, methods=['get'], permission_classes=[IsAdmin])
    def users(self, request, pk=None):
        """
        Récupère la liste des utilisateurs utilisant ce profil.
        Inclut la pagination et utilise select_related pour optimiser les requêtes.
        """
        profile = self.get_object()
        # Utiliser select_related pour éviter les N+1 queries
        users_queryset = profile.users.filter(is_active=True).select_related('promotion')

        # Pagination manuelle
        paginator = LargeResultsSetPagination()
        paginated_users = paginator.paginate_queryset(users_queryset, request)

        users_data = []
        for user in paginated_users:
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

        return paginator.get_paginated_response({
            'profile': {'id': profile.id, 'name': profile.name},
            'users': users_data
        })

    @action(detail=True, methods=['get'], permission_classes=[IsAdmin])
    def promotions(self, request, pk=None):
        """
        Récupère la liste des promotions utilisant ce profil.
        Utilise prefetch_related pour optimiser le comptage des utilisateurs.
        """
        from django.db.models import Count

        profile = self.get_object()
        # Utiliser annotate pour éviter les N+1 queries sur users.count()
        promotions = profile.promotions.filter(is_active=True).annotate(
            user_count=Count('users', filter=models.Q(users__is_active=True))
        )

        # Pagination manuelle
        paginator = StandardResultsSetPagination()
        paginated_promotions = paginator.paginate_queryset(promotions, request)

        promotions_data = []
        for promotion in paginated_promotions:
            promotions_data.append({
                'id': promotion.id,
                'name': promotion.name,
                'is_active': promotion.is_active,
                'user_count': promotion.user_count
            })

        return paginator.get_paginated_response({
            'profile': {'id': profile.id, 'name': profile.name},
            'promotions': promotions_data
        })

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Liste des profils actifs uniquement"""
        active_profiles = Profile.objects.filter(is_active=True)
        serializer = self.get_serializer(active_profiles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdmin])
    def statistics(self, request):
        """
        Statistiques globales sur tous les profils.
        Retourne des données agrégées pour le dashboard admin.

        ADMIN ONLY - Contient des données sensibles sur l'utilisation.
        Optimisé avec des requêtes agrégées pour éviter les N+1.
        """
        from django.db.models import Count, Sum, Avg, Q

        # Utiliser des requêtes optimisées avec annotate
        profiles = Profile.objects.annotate(
            direct_users_count=Count(
                'users',
                filter=Q(users__is_active=True)
            )
        )

        # Statistiques générales (requêtes agrégées, pas de boucle)
        stats = Profile.objects.aggregate(
            total_profiles=Count('id'),
            active_profiles=Count('id', filter=Q(is_active=True)),
            unlimited_profiles=Count('id', filter=Q(quota_type='unlimited')),
            limited_profiles=Count('id', filter=Q(quota_type='limited'))
        )

        total_profiles = stats['total_profiles']
        active_profiles_count = stats['active_profiles']
        inactive_profiles = total_profiles - active_profiles_count

        # Pagination pour les profils avec statistiques
        paginator = LargeResultsSetPagination()
        paginated_profiles = paginator.paginate_queryset(profiles, request)

        profiles_with_stats = []
        for profile in paginated_profiles:
            # Utilisateurs via promotions (requête optimisée)
            promotion_users = User.objects.filter(
                promotion__profile=profile,
                is_active=True,
                profile__isnull=True
            ).count()

            total_users = profile.direct_users_count + promotion_users

            # Consommation moyenne pour ce profil (requête agrégée unique)
            avg_usage = UserProfileUsage.objects.filter(
                user__profile=profile,
                is_active=True
            ).aggregate(
                avg_today=Avg('used_today'),
                avg_week=Avg('used_week'),
                avg_month=Avg('used_month'),
                avg_total=Avg('used_total'),
                exceeded_count=Count('id', filter=Q(is_exceeded=True))
            )

            exceeded_count = avg_usage['exceeded_count'] or 0

            profiles_with_stats.append({
                'profile_id': profile.id,
                'profile_name': profile.name,
                'quota_type': profile.quota_type,
                'is_active': profile.is_active,
                'direct_users': profile.direct_users_count,
                'promotion_users': promotion_users,
                'total_users': total_users,
                'avg_usage_today_gb': round(avg_usage['avg_today'] / (1024**3), 2) if avg_usage['avg_today'] else 0,
                'avg_usage_week_gb': round(avg_usage['avg_week'] / (1024**3), 2) if avg_usage['avg_week'] else 0,
                'avg_usage_month_gb': round(avg_usage['avg_month'] / (1024**3), 2) if avg_usage['avg_month'] else 0,
                'avg_usage_total_gb': round(avg_usage['avg_total'] / (1024**3), 2) if avg_usage['avg_total'] else 0,
                'exceeded_count': exceeded_count,
                'exceeded_percent': round((exceeded_count / total_users * 100), 2) if total_users > 0 else 0
            })

        # Trier par nombre d'utilisateurs
        profiles_with_stats.sort(key=lambda x: x['total_users'], reverse=True)

        # Top 5 profils
        top_profiles = profiles_with_stats[:5]

        return paginator.get_paginated_response({
            'summary': {
                'total_profiles': total_profiles,
                'active_profiles': active_profiles_count,
                'inactive_profiles': inactive_profiles,
                'unlimited_profiles': stats['unlimited_profiles'],
                'limited_profiles': stats['limited_profiles'],
            },
            'top_profiles': top_profiles,
            'profiles': profiles_with_stats
        })

    @action(detail=True, methods=['get'])
    def statistics_detail(self, request, pk=None):
        """
        Statistiques détaillées pour un profil spécifique.
        """
        from django.db.models import Avg, Max, Min, Sum

        profile = self.get_object()

        # Utilisateurs utilisant ce profil
        direct_users = User.objects.filter(profile=profile, is_active=True)
        promotion_users = User.objects.filter(
            promotion__profile=profile,
            is_active=True,
            profile__isnull=True
        )

        all_users = direct_users.count() + promotion_users.count()

        # Statistiques d'utilisation
        usages = UserProfileUsage.objects.filter(
            user__in=list(direct_users) + list(promotion_users),
            is_active=True
        )

        usage_stats = usages.aggregate(
            avg_today=Avg('used_today'),
            avg_week=Avg('used_week'),
            avg_month=Avg('used_month'),
            avg_total=Avg('used_total'),
            max_total=Max('used_total'),
            min_total=Min('used_total'),
            total_consumed=Sum('used_total')
        )

        # Répartition par statut
        exceeded_users = usages.filter(is_exceeded=True).count()
        active_users = usages.filter(is_exceeded=False).count()

        # Répartition par tranche de consommation (% du quota)
        if profile.quota_type == 'limited':
            ranges = {
                '0-25%': 0,
                '25-50%': 0,
                '50-75%': 0,
                '75-100%': 0,
                '>100%': 0
            }

            for usage in usages:
                percent = usage.total_usage_percent
                if percent < 25:
                    ranges['0-25%'] += 1
                elif percent < 50:
                    ranges['25-50%'] += 1
                elif percent < 75:
                    ranges['50-75%'] += 1
                elif percent <= 100:
                    ranges['75-100%'] += 1
                else:
                    ranges['>100%'] += 1
        else:
            ranges = None

        return Response({
            'profile': {
                'id': profile.id,
                'name': profile.name,
                'quota_type': profile.quota_type,
                'data_volume_gb': profile.data_volume_gb,
                'bandwidth_upload_mbps': profile.bandwidth_upload_mbps,
                'bandwidth_download_mbps': profile.bandwidth_download_mbps,
            },
            'users': {
                'direct': direct_users.count(),
                'via_promotion': promotion_users.count(),
                'total': all_users,
                'exceeded': exceeded_users,
                'active': active_users,
            },
            'consumption': {
                'avg_today_gb': round(usage_stats['avg_today'] / (1024**3), 2) if usage_stats['avg_today'] else 0,
                'avg_week_gb': round(usage_stats['avg_week'] / (1024**3), 2) if usage_stats['avg_week'] else 0,
                'avg_month_gb': round(usage_stats['avg_month'] / (1024**3), 2) if usage_stats['avg_month'] else 0,
                'avg_total_gb': round(usage_stats['avg_total'] / (1024**3), 2) if usage_stats['avg_total'] else 0,
                'max_total_gb': round(usage_stats['max_total'] / (1024**3), 2) if usage_stats['max_total'] else 0,
                'min_total_gb': round(usage_stats['min_total'] / (1024**3), 2) if usage_stats['min_total'] else 0,
                'total_consumed_gb': round(usage_stats['total_consumed'] / (1024**3), 2) if usage_stats['total_consumed'] else 0,
            },
            'distribution': ranges
        })


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
        """
        Désactive l'utilisateur dans FreeRADIUS (statut=0).
        Utilise select_for_update() pour éviter les race conditions.
        """
        from radius.models import RadCheck

        try:
            with transaction.atomic():
                user = User.objects.select_for_update(nowait=True).get(pk=pk)

                if not user.is_radius_activated:
                    return Response(
                        format_api_error(
                            'not_activated',
                            f'L\'utilisateur {user.username} n\'est pas encore activé dans RADIUS.'
                        ),
                        status=status.HTTP_400_BAD_REQUEST
                    )

                updated = RadCheck.objects.filter(username=user.username).update(statut=False)

                # Mettre à jour le statut local
                user.is_radius_enabled = False
                user.save(update_fields=['is_radius_enabled'])

                return Response(format_api_success(
                    f'Utilisateur {user.username} désactivé dans RADIUS.',
                    {
                        'username': user.username,
                        'status': 'disabled',
                        'radcheck_updated': updated
                    }
                ))

        except User.DoesNotExist:
            raise ResourceNotFoundError(detail=f'Utilisateur avec ID {pk} non trouvé.')
        except transaction.DatabaseError:
            raise RaceConditionError(
                detail='L\'utilisateur est en cours de modification. Veuillez réessayer.'
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def activate_radius(self, request, pk=None):
        """
        Active l'utilisateur dans FreeRADIUS avec les paramètres de son profil.
        Utilise select_for_update() pour éviter les race conditions.
        """
        from radius.models import RadCheck, RadReply, RadUserGroup

        try:
            with transaction.atomic():
                # Verrouiller l'utilisateur pour éviter les race conditions
                user = User.objects.select_for_update(nowait=True).get(pk=pk)

                # Vérifier si déjà activé
                if user.is_radius_activated and user.is_radius_enabled:
                    return Response(
                        format_api_error(
                            'already_activated',
                            f'L\'utilisateur {user.username} est déjà activé dans RADIUS.'
                        ),
                        status=status.HTTP_409_CONFLICT
                    )

                if not user.cleartext_password:
                    raise RadiusActivationError(
                        detail='Mot de passe en clair indisponible pour cet utilisateur. '
                               'L\'utilisateur doit se réinscrire ou un admin doit réinitialiser son mot de passe.'
                    )

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
                    # Validation des valeurs de bande passante
                    upload_mbps = max(1, int(profile.bandwidth_upload))
                    download_mbps = max(1, int(profile.bandwidth_download))
                    bandwidth_value = f"{upload_mbps}M/{download_mbps}M"
                else:
                    bandwidth_value = '10M/10M'

                RadReply.objects.update_or_create(
                    username=user.username,
                    attribute='Mikrotik-Rate-Limit',
                    defaults={'op': '=', 'value': bandwidth_value}
                )

                # 5. radcheck - Quota de données (si le profil a un quota limité)
                if profile and profile.quota_type == 'limited':
                    RadCheck.objects.update_or_create(
                        username=user.username,
                        attribute='ChilliSpot-Max-Total-Octets',
                        defaults={'op': ':=', 'value': str(profile.data_volume), 'statut': True}
                    )

                # 6. radusergroup - Groupe utilisateur
                RadUserGroup.objects.update_or_create(
                    username=user.username,
                    groupname=user.role,
                    defaults={'priority': 0}
                )

                # Mettre à jour les statuts
                user.is_radius_activated = True
                user.is_radius_enabled = True
                user.save(update_fields=['is_radius_activated', 'is_radius_enabled'])

                return Response(format_api_success(
                    f'Utilisateur {user.username} activé avec succès dans RADIUS.',
                    {
                        'username': user.username,
                        'status': 'enabled',
                        'profile': profile.name if profile else 'Default',
                        'bandwidth': bandwidth_value,
                        'session_timeout': session_timeout,
                        'quota_type': profile.quota_type if profile else 'unlimited'
                    }
                ))

        except User.DoesNotExist:
            raise ResourceNotFoundError(detail=f'Utilisateur avec ID {pk} non trouvé.')
        except transaction.DatabaseError:
            raise RaceConditionError(
                detail='L\'utilisateur est en cours de modification par une autre opération. Veuillez réessayer.'
            )


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
    """
    ViewSet for Voucher model.

    Toutes les actions nécessitent une authentification.
    - validate: Vérifie si un voucher est valide (authentifié)
    - redeem: Utilise un voucher (authentifié)
    - active: Liste les vouchers actifs (admin uniquement)
    """
    queryset = Voucher.objects.all()
    serializer_class = VoucherSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """
        Permissions:
        - validate/redeem: Utilisateur authentifié
        - create/update/delete: Admin uniquement
        - list/retrieve: Authentifié (filtré par utilisateur)
        """
        if self.action in ['validate', 'redeem']:
            # CORRECTION: Authentification requise pour éviter le brute-force
            return [permissions.IsAuthenticated()]
        elif self.action in ['create', 'update', 'partial_update', 'destroy', 'active']:
            return [IsAdmin()]
        return super().get_permissions()

    def get_queryset(self):
        """Filtre les vouchers selon le rôle de l'utilisateur"""
        user = self.request.user
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            # Admins voient tous les vouchers
            return Voucher.objects.all().select_related('used_by', 'created_by')
        elif user.is_authenticated:
            # Utilisateurs normaux voient seulement leurs vouchers utilisés
            return Voucher.objects.filter(used_by=user).select_related('created_by')
        return Voucher.objects.none()

    def perform_create(self, serializer):
        """Set created_by to current user"""
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    @rate_limit(key_prefix='voucher_validate', rate='10/m', method='POST', block_duration=120)
    def validate(self, request):
        """
        Valide un code voucher.

        Retourne les informations du voucher s'il est valide.
        Gère proprement les erreurs de voucher non trouvé, expiré ou déjà utilisé.
        """
        serializer = VoucherValidationSerializer(data=request.data)
        if not serializer.is_valid():
            raise DRFValidationError(detail=serializer.errors)

        code = serializer.validated_data['code']

        try:
            voucher = Voucher.objects.select_related('used_by', 'created_by').get(code=code)
        except Voucher.DoesNotExist:
            raise VoucherNotFoundError(
                detail=f'Le code voucher "{code}" n\'existe pas.'
            )

        # Vérifier l'état du voucher
        if voucher.status == 'expired':
            raise VoucherExpiredError(
                detail='Ce voucher a expiré et ne peut plus être utilisé.'
            )

        if voucher.status == 'used':
            raise VoucherAlreadyUsedError(
                detail='Ce voucher a atteint sa limite d\'utilisation.'
            )

        if voucher.status == 'revoked':
            raise VoucherValidationError(
                detail='Ce voucher a été révoqué par un administrateur.'
            )

        # Vérifier la validité temporelle
        now = timezone.now()
        if voucher.valid_from and now < voucher.valid_from:
            raise VoucherValidationError(
                detail=f'Ce voucher n\'est pas encore valide. '
                       f'Il sera actif à partir du {voucher.valid_from.strftime("%d/%m/%Y %H:%M")}.'
            )

        if voucher.valid_until and now > voucher.valid_until:
            # Mettre à jour le statut du voucher
            voucher.status = 'expired'
            voucher.save(update_fields=['status'])
            raise VoucherExpiredError(
                detail=f'Ce voucher a expiré le {voucher.valid_until.strftime("%d/%m/%Y %H:%M")}.'
            )

        voucher_serializer = VoucherSerializer(voucher)
        return Response(format_api_success(
            'Le voucher est valide.',
            {
                'valid': True,
                'voucher': voucher_serializer.data,
                'remaining_uses': voucher.max_devices - voucher.used_count
            }
        ))

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    @rate_limit(key_prefix='voucher_redeem', rate='5/h', method='POST', block_duration=300)
    def redeem(self, request):
        """
        Utilise (redemption) un code voucher.

        L'utilisateur doit être authentifié.
        Utilise une transaction atomique pour éviter les race conditions.
        """
        serializer = VoucherValidationSerializer(data=request.data)
        if not serializer.is_valid():
            raise DRFValidationError(detail=serializer.errors)

        code = serializer.validated_data['code']

        try:
            with transaction.atomic():
                # Verrouiller le voucher pour éviter les race conditions
                try:
                    voucher = Voucher.objects.select_for_update(nowait=True).get(code=code)
                except Voucher.DoesNotExist:
                    raise VoucherNotFoundError(
                        detail=f'Le code voucher "{code}" n\'existe pas.'
                    )

                # Vérifications de validité
                if voucher.status == 'expired':
                    raise VoucherExpiredError(
                        detail='Ce voucher a expiré et ne peut plus être utilisé.'
                    )

                if voucher.status == 'used':
                    raise VoucherAlreadyUsedError(
                        detail='Ce voucher a atteint sa limite d\'utilisation.'
                    )

                if voucher.status == 'revoked':
                    raise VoucherValidationError(
                        detail='Ce voucher a été révoqué par un administrateur.'
                    )

                # Vérifier la validité temporelle
                now = timezone.now()
                if voucher.valid_from and now < voucher.valid_from:
                    raise VoucherValidationError(
                        detail=f'Ce voucher n\'est pas encore valide.'
                    )

                if voucher.valid_until and now > voucher.valid_until:
                    voucher.status = 'expired'
                    voucher.save(update_fields=['status'])
                    raise VoucherExpiredError(
                        detail='Ce voucher a expiré.'
                    )

                # Utiliser le voucher
                voucher.used_by = request.user
                voucher.used_at = now
                voucher.used_count += 1

                # Mettre à jour le statut si limite atteinte
                if voucher.used_count >= voucher.max_devices:
                    voucher.status = 'used'

                voucher.save()

                return Response(format_api_success(
                    'Voucher utilisé avec succès.',
                    {
                        'code': voucher.code,
                        'duration_seconds': voucher.duration,
                        'duration_hours': round(voucher.duration / 3600, 2) if voucher.duration else None,
                        'remaining_uses': max(0, voucher.max_devices - voucher.used_count),
                        'status': voucher.status
                    }
                ))

        except transaction.DatabaseError:
            raise RaceConditionError(
                detail='Le voucher est en cours d\'utilisation par une autre opération. Veuillez réessayer.'
            )

    @action(detail=False, methods=['get'], permission_classes=[IsAdmin])
    def active(self, request):
        """Get all active vouchers (admin only)"""
        vouchers = Voucher.objects.filter(status='active').select_related('used_by', 'created_by')
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
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Optimise les requêtes avec select_related"""
        return Promotion.objects.all().select_related('profile')

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def active(self, request):
        """Liste des promotions actives (accessible publiquement pour l'inscription)"""
        active_promotions = Promotion.objects.filter(is_active=True).select_related('profile')
        serializer = self.get_serializer(active_promotions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[IsAdmin])
    def users(self, request, pk=None):
        """
        Récupère la liste des utilisateurs d'une promotion avec leurs statuts RADIUS.
        Inclut la pagination et optimise les requêtes avec select_related.
        """
        promotion = self.get_object()
        # Optimiser les requêtes avec select_related
        users_queryset = promotion.users.filter(is_active=True).select_related(
            'promotion', 'profile'
        )

        # Pagination
        paginator = LargeResultsSetPagination()
        paginated_users = paginator.paginate_queryset(users_queryset, request)

        users_data = []
        for user in paginated_users:
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

        return paginator.get_paginated_response({
            'promotion': {
                'id': promotion.id,
                'name': promotion.name,
                'is_active': promotion.is_active
            },
            'users': users_data
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def deactivate(self, request, pk=None):
        """
        Désactive une promotion et SUPPRIME tous les utilisateurs de RADIUS.
        Les utilisateurs n'auront plus accès à Internet.
        Utilise une transaction atomique pour garantir la cohérence.
        """
        from radius.models import RadReply, RadUserGroup

        try:
            with transaction.atomic():
                # Verrouiller la promotion pour éviter les race conditions
                promotion = Promotion.objects.select_for_update(nowait=True).get(pk=pk)

                if not promotion.is_active:
                    return Response(
                        format_api_error(
                            'already_deactivated',
                            f'La promotion "{promotion.name}" est déjà désactivée.'
                        ),
                        status=status.HTTP_400_BAD_REQUEST
                    )

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
                        errors.append({'username': user.username, 'error': str(e)})

                return Response(format_api_success(
                    f'Promotion "{promotion.name}" désactivée. {disabled_count} utilisateur(s) supprimé(s) de RADIUS.',
                    {
                        'promotion': {
                            'id': promotion.id,
                            'name': promotion.name,
                            'is_active': promotion.is_active
                        },
                        'users_disabled': disabled_count,
                        'users_failed': failed_count,
                        'errors': errors if errors else None
                    }
                ))

        except Promotion.DoesNotExist:
            raise ResourceNotFoundError(detail=f'Promotion avec ID {pk} non trouvée.')
        except transaction.DatabaseError:
            raise RaceConditionError(
                detail='La promotion est en cours de modification. Veuillez réessayer.'
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def activate(self, request, pk=None):
        """
        Active une promotion et CRÉE les entrées RADIUS pour TOUS les utilisateurs.
        Tous les utilisateurs auront accès à Internet.
        Utilise une transaction atomique pour garantir la cohérence.
        """
        from radius.models import RadReply, RadUserGroup

        try:
            with transaction.atomic():
                # Verrouiller la promotion pour éviter les race conditions
                promotion = Promotion.objects.select_for_update(nowait=True).get(pk=pk)

                if promotion.is_active:
                    return Response(
                        format_api_error(
                            'already_activated',
                            f'La promotion "{promotion.name}" est déjà activée.'
                        ),
                        status=status.HTTP_400_BAD_REQUEST
                    )

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
                            errors.append({
                                'username': user.username,
                                'error': 'Mot de passe en clair non disponible'
                            })
                            continue

                        # CRÉER les entrées RADIUS avec les paramètres du profil
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

                        # 2. radreply - Session timeout
                        session_timeout = profile.session_timeout if profile else (86400 if user.is_staff else 3600)
                        RadReply.objects.update_or_create(
                            username=user.username,
                            attribute='Session-Timeout',
                            defaults={'op': '=', 'value': str(session_timeout)}
                        )

                        # 3. radreply - Idle timeout
                        if profile:
                            RadReply.objects.update_or_create(
                                username=user.username,
                                attribute='Idle-Timeout',
                                defaults={'op': '=', 'value': str(profile.idle_timeout)}
                            )

                        # 4. radreply - Limite de bande passante
                        if profile:
                            upload_mbps = max(1, int(profile.bandwidth_upload))
                            download_mbps = max(1, int(profile.bandwidth_download))
                            bandwidth_value = f"{upload_mbps}M/{download_mbps}M"
                        else:
                            bandwidth_value = '10M/10M'

                        RadReply.objects.update_or_create(
                            username=user.username,
                            attribute='Mikrotik-Rate-Limit',
                            defaults={'op': '=', 'value': bandwidth_value}
                        )

                        # 5. radcheck - Quota de données
                        if profile and profile.quota_type == 'limited':
                            RadCheck.objects.update_or_create(
                                username=user.username,
                                attribute='ChilliSpot-Max-Total-Octets',
                                defaults={'op': ':=', 'value': str(profile.data_volume), 'statut': True}
                            )

                        # 6. radusergroup - Groupe utilisateur
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
                        errors.append({'username': user.username, 'error': str(e)})

                return Response(format_api_success(
                    f'Promotion "{promotion.name}" activée. {enabled_count} utilisateur(s) créé(s) dans RADIUS.',
                    {
                        'promotion': {
                            'id': promotion.id,
                            'name': promotion.name,
                            'is_active': promotion.is_active
                        },
                        'users_enabled': enabled_count,
                        'users_failed': failed_count,
                        'errors': errors if errors else None
                    }
                ))

        except Promotion.DoesNotExist:
            raise ResourceNotFoundError(detail=f'Promotion avec ID {pk} non trouvée.')
        except transaction.DatabaseError:
            raise RaceConditionError(
                detail='La promotion est en cours de modification. Veuillez réessayer.'
            )


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


class UserProfileUsageViewSet(viewsets.ModelViewSet):
    """ViewSet for UserProfileUsage model"""
    queryset = UserProfileUsage.objects.all()
    serializer_class = UserProfileUsageSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        """Permet aux utilisateurs de voir leur propre usage"""
        user = self.request.user
        if user.is_staff or user.is_superuser:
            # Admins see all usages
            return UserProfileUsage.objects.all().select_related('user')
        # Regular users see only their own usage
        return UserProfileUsage.objects.filter(user=user)

    @action(detail=True, methods=['post'])
    def reset_daily(self, request, pk=None):
        """Réinitialise le compteur journalier"""
        usage = self.get_object()
        usage.reset_daily()
        serializer = self.get_serializer(usage)
        return Response({
            'status': 'success',
            'message': 'Compteur journalier réinitialisé',
            'usage': serializer.data
        })

    @action(detail=True, methods=['post'])
    def reset_weekly(self, request, pk=None):
        """Réinitialise le compteur hebdomadaire"""
        usage = self.get_object()
        usage.reset_weekly()
        serializer = self.get_serializer(usage)
        return Response({
            'status': 'success',
            'message': 'Compteur hebdomadaire réinitialisé',
            'usage': serializer.data
        })

    @action(detail=True, methods=['post'])
    def reset_monthly(self, request, pk=None):
        """Réinitialise le compteur mensuel"""
        usage = self.get_object()
        usage.reset_monthly()
        serializer = self.get_serializer(usage)
        return Response({
            'status': 'success',
            'message': 'Compteur mensuel réinitialisé',
            'usage': serializer.data
        })

    @action(detail=True, methods=['post'])
    def reset_all(self, request, pk=None):
        """Réinitialise tous les compteurs"""
        usage = self.get_object()
        usage.reset_all()
        serializer = self.get_serializer(usage)
        return Response({
            'status': 'success',
            'message': 'Tous les compteurs réinitialisés',
            'usage': serializer.data
        })

    @action(detail=True, methods=['post'])
    def add_usage(self, request, pk=None):
        """Ajoute de la consommation (pour tests ou intégration externe)"""
        usage = self.get_object()
        bytes_used = request.data.get('bytes_used', 0)

        if bytes_used <= 0:
            return Response(
                {'error': 'bytes_used must be positive'},
                status=status.HTTP_400_BAD_REQUEST
            )

        usage.add_usage(bytes_used)
        serializer = self.get_serializer(usage)
        return Response({
            'status': 'success',
            'message': f'{bytes_used} octets ajoutés',
            'usage': serializer.data
        })

    @action(detail=False, methods=['get'])
    def my_usage(self, request):
        """Récupère l'utilisation de l'utilisateur connecté"""
        user = request.user
        try:
            usage = UserProfileUsage.objects.get(user=user)
            serializer = self.get_serializer(usage)
            return Response(serializer.data)
        except UserProfileUsage.DoesNotExist:
            return Response(
                {'error': 'Aucune utilisation trouvée pour cet utilisateur'},
                status=status.HTTP_404_NOT_FOUND
            )


class ProfileHistoryViewSet(viewsets.ModelViewSet):
    """ViewSet for ProfileHistory model"""
    queryset = ProfileHistory.objects.all()
    serializer_class = ProfileHistorySerializer
    permission_classes = [IsAdmin]
    http_method_names = ['get', 'post', 'head', 'options']  # Read-only + POST

    def get_queryset(self):
        """Filtre par utilisateur si spécifié"""
        queryset = ProfileHistory.objects.all().select_related(
            'user', 'old_profile', 'new_profile', 'changed_by'
        )

        # Filtrer par utilisateur
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Filtrer par profil
        profile_id = self.request.query_params.get('profile')
        if profile_id:
            queryset = queryset.filter(
                models.Q(old_profile_id=profile_id) | models.Q(new_profile_id=profile_id)
            )

        return queryset.order_by('-changed_at')

    @action(detail=False, methods=['get'])
    def user_history(self, request):
        """Récupère l'historique des changements de profil pour un utilisateur"""
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        history = ProfileHistory.objects.filter(user_id=user_id).select_related(
            'old_profile', 'new_profile', 'changed_by'
        ).order_by('-changed_at')

        serializer = self.get_serializer(history, many=True)
        return Response(serializer.data)


class ProfileAlertViewSet(viewsets.ModelViewSet):
    """ViewSet for ProfileAlert model"""
    queryset = ProfileAlert.objects.all()
    serializer_class = ProfileAlertSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        """Filtre par profil si spécifié"""
        queryset = ProfileAlert.objects.all().select_related('profile', 'created_by')

        # Filtrer par profil
        profile_id = self.request.query_params.get('profile')
        if profile_id:
            queryset = queryset.filter(profile_id=profile_id)

        # Filtrer par statut actif
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset.order_by('-created_at')

    @action(detail=False, methods=['post'])
    def check_alerts(self, request):
        """Vérifie les alertes pour tous les utilisateurs et retourne celles déclenchées"""
        triggered_alerts = []

        # Récupérer toutes les alertes actives
        alerts = ProfileAlert.objects.filter(is_active=True).select_related('profile')

        # Récupérer toutes les utilisations avec profil
        usages = UserProfileUsage.objects.filter(is_active=True).select_related('user')

        for usage in usages:
            profile = usage.get_effective_profile()
            if not profile:
                continue

            # Vérifier les alertes pour ce profil
            profile_alerts = alerts.filter(profile=profile)

            for alert in profile_alerts:
                if alert.should_trigger(usage):
                    triggered_alerts.append({
                        'alert_id': alert.id,
                        'alert_type': alert.alert_type,
                        'user_id': usage.user.id,
                        'username': usage.user.username,
                        'profile_name': profile.name,
                        'threshold': alert.threshold_percent,
                        'current_usage_percent': usage.total_usage_percent,
                        'days_remaining': usage.days_remaining(),
                        'message': self._format_alert_message(alert, usage)
                    })

        return Response({
            'triggered_count': len(triggered_alerts),
            'alerts': triggered_alerts
        })

    def _format_alert_message(self, alert, usage):
        """Formate le message d'alerte avec les données de l'utilisateur"""
        if alert.message_template:
            return alert.message_template.format(
                username=usage.user.username,
                percent=round(usage.total_usage_percent, 2),
                remaining_gb=round(
                    (usage.get_effective_profile().data_volume - usage.used_total) / (1024**3),
                    2
                ) if usage.get_effective_profile() else 0,
                days_remaining=usage.days_remaining() or 0
            )
        else:
            # Message par défaut
            if alert.alert_type in ['quota_warning', 'quota_critical']:
                return f"Attention: {round(usage.total_usage_percent, 2)}% de votre quota utilisé"
            else:
                return f"Votre profil expire dans {usage.days_remaining()} jour(s)"


class UserDisconnectionLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for UserDisconnectionLog - Read only for users, full access for admins

    Permet de:
    - Lister les logs de déconnexion
    - Voir le statut actuel de déconnexion d'un utilisateur
    - (Admin) Réactiver un utilisateur
    """
    queryset = UserDisconnectionLog.objects.all()
    serializer_class = UserDisconnectionLogSerializer

    def get_permissions(self):
        """Permissions personnalisées selon l'action"""
        if self.action in ['reactivate_user', 'list', 'retrieve']:
            permission_classes = [IsAdmin]
        else:
            permission_classes = [IsAuthenticatedUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Filtre les logs selon l'utilisateur"""
        user = self.request.user

        if user.is_staff or user.is_superuser:
            # Les admins voient tous les logs
            queryset = UserDisconnectionLog.objects.all()
        else:
            # Les utilisateurs ne voient que leurs propres logs
            queryset = UserDisconnectionLog.objects.filter(user=user)

        # Filtres optionnels
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        reason = self.request.query_params.get('reason', None)
        if reason:
            queryset = queryset.filter(reason=reason)

        return queryset.select_related('user', 'reconnected_by')

    @action(detail=False, methods=['get'], url_path='current')
    def current_disconnection(self, request):
        """
        Retourne la déconnexion active de l'utilisateur connecté

        GET /api/core/disconnection-logs/current/
        """
        try:
            log = UserDisconnectionLog.objects.filter(
                user=request.user,
                is_active=True
            ).select_related('user').latest('disconnected_at')

            serializer = self.get_serializer(log)
            return Response(serializer.data)
        except UserDisconnectionLog.DoesNotExist:
            return Response({
                'is_disconnected': False,
                'message': 'Aucune déconnexion active'
            }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='reactivate', permission_classes=[IsAdmin])
    def reactivate_user(self, request, pk=None):
        """
        Réactive un utilisateur en marquant la déconnexion comme résolue
        et en mettant à jour le statut dans radcheck

        POST /api/core/disconnection-logs/{id}/reactivate/
        """
        log = self.get_object()

        if not log.is_active:
            return Response({
                'error': 'Cette déconnexion a déjà été résolue'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            with models.transaction.atomic():
                # Réactiver le log
                log.reactivate(admin_user=request.user)

                # Mettre à jour statut=1 dans radcheck
                updated = RadCheck.objects.filter(
                    username=log.user.username
                ).update(statut=True)

                return Response({
                    'message': f'Utilisateur {log.user.username} réactivé avec succès',
                    'radcheck_updated': updated,
                    'reconnected_at': log.reconnected_at,
                    'reconnected_by': request.user.username
                })
        except Exception as e:
            return Response({
                'error': f'Erreur lors de la réactivation: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

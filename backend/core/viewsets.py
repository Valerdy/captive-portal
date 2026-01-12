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

    def destroy(self, request, *args, **kwargs):
        """
        Supprime un profil avec gestion des erreurs et nettoyage des relations.

        Vérifie si des utilisateurs ou promotions utilisent ce profil avant suppression.
        """
        import logging
        import traceback
        logger = logging.getLogger(__name__)

        try:
            profile = self.get_object()
            profile_name = profile.name
            profile_id = profile.id

            # Vérifier si des utilisateurs utilisent ce profil directement
            users_with_profile = profile.users.filter(is_active=True).count()
            if users_with_profile > 0:
                return Response(
                    format_api_error(
                        'profile_in_use',
                        f'Ce profil est utilisé par {users_with_profile} utilisateur(s) actif(s). '
                        'Veuillez d\'abord réassigner ces utilisateurs à un autre profil.'
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Vérifier si des promotions utilisent ce profil
            promotions_with_profile = profile.promotions.filter(is_active=True).count()
            if promotions_with_profile > 0:
                return Response(
                    format_api_error(
                        'profile_in_use',
                        f'Ce profil est utilisé par {promotions_with_profile} promotion(s) active(s). '
                        'Veuillez d\'abord réassigner ces promotions à un autre profil.'
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Supprimer le profil (les signaux gèrent la synchronisation MikroTik)
            self.perform_destroy(profile)

            logger.info(f"Profile '{profile_name}' (ID: {profile_id}) deleted successfully")
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            error_msg = str(e)
            error_traceback = traceback.format_exc()
            logger.error(f"Error deleting profile: {error_msg}\n{error_traceback}")
            return Response(
                format_api_error(
                    'deletion_failed',
                    f'Erreur lors de la suppression du profil: {error_msg}'
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
        Inclut les utilisateurs directs ET ceux via promotion.
        Utilise la pagination et select_related pour optimiser les requêtes.
        """
        from django.db.models import Q

        profile = self.get_object()

        # Utilisateurs directs (profil assigné directement)
        direct_users = profile.users.filter(is_active=True).select_related('promotion')

        # Utilisateurs via promotion (pas de profil direct, mais promotion avec ce profil)
        promotion_users = User.objects.filter(
            Q(profile__isnull=True) & Q(promotion__profile=profile) & Q(is_active=True)
        ).select_related('promotion')

        # Combiner les deux querysets
        from itertools import chain
        all_users = list(chain(direct_users, promotion_users))

        # Pagination manuelle
        paginator = LargeResultsSetPagination()
        paginated_users = paginator.paginate_queryset(all_users, request)

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
                'assignment_type': 'direct' if user.profile == profile else 'via_promotion',
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
        ).order_by('name')

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

        Fix #11: Optimisé avec requêtes agrégées pré-calculées pour éviter N+1.
        - Pré-calcul des utilisateurs via promotion en une seule requête
        - Pré-calcul des statistiques d'usage par profil
        """
        from django.db.models import Count, Sum, Avg, Q, Subquery, OuterRef, IntegerField
        from django.db.models.functions import Coalesce

        # === REQUÊTE 1: Statistiques générales (1 requête) ===
        stats = Profile.objects.aggregate(
            total_profiles=Count('id'),
            active_profiles=Count('id', filter=Q(is_active=True)),
            unlimited_profiles=Count('id', filter=Q(quota_type='unlimited')),
            limited_profiles=Count('id', filter=Q(quota_type='limited'))
        )

        total_profiles = stats['total_profiles']
        active_profiles_count = stats['active_profiles']
        inactive_profiles = total_profiles - active_profiles_count

        # === FIX #11: Pré-calcul des utilisateurs via promotion (1 requête) ===
        promotion_users_subquery = User.objects.filter(
            promotion__profile=OuterRef('pk'),
            is_active=True,
            profile__isnull=True
        ).values('promotion__profile').annotate(
            cnt=Count('id')
        ).values('cnt')

        # === REQUÊTE 2: Profils avec annotations pré-calculées (1 requête) ===
        profiles = Profile.objects.annotate(
            direct_users_count=Count(
                'users',
                filter=Q(users__is_active=True)
            ),
            promotion_users_count=Coalesce(
                Subquery(promotion_users_subquery, output_field=IntegerField()),
                0
            )
        ).order_by('-direct_users_count')

        # === FIX #11: Pré-calcul des stats d'usage par profil (1 requête) ===
        usage_stats_by_profile = {}
        usage_aggregates = UserProfileUsage.objects.filter(
            is_active=True,
            user__profile__isnull=False
        ).values('user__profile_id').annotate(
            avg_today=Avg('used_today'),
            avg_week=Avg('used_week'),
            avg_month=Avg('used_month'),
            avg_total=Avg('used_total'),
            exceeded_count=Count('id', filter=Q(is_exceeded=True))
        )

        for agg in usage_aggregates:
            usage_stats_by_profile[agg['user__profile_id']] = agg

        # Pagination
        paginator = LargeResultsSetPagination()
        paginated_profiles = paginator.paginate_queryset(profiles, request)

        # === Construction des résultats (pas de requête supplémentaire) ===
        profiles_with_stats = []
        for profile in paginated_profiles:
            total_users = profile.direct_users_count + profile.promotion_users_count

            # Récupérer les stats pré-calculées
            usage = usage_stats_by_profile.get(profile.id, {})

            exceeded_count = usage.get('exceeded_count', 0) or 0

            profiles_with_stats.append({
                'profile_id': profile.id,
                'profile_name': profile.name,
                'quota_type': profile.quota_type,
                'is_active': profile.is_active,
                'direct_users': profile.direct_users_count,
                'promotion_users': profile.promotion_users_count,
                'total_users': total_users,
                'avg_usage_today_gb': round(usage.get('avg_today', 0) / (1024**3), 2) if usage.get('avg_today') else 0,
                'avg_usage_week_gb': round(usage.get('avg_week', 0) / (1024**3), 2) if usage.get('avg_week') else 0,
                'avg_usage_month_gb': round(usage.get('avg_month', 0) / (1024**3), 2) if usage.get('avg_month') else 0,
                'avg_usage_total_gb': round(usage.get('avg_total', 0) / (1024**3), 2) if usage.get('avg_total') else 0,
                'exceeded_count': exceeded_count,
                'exceeded_percent': round((exceeded_count / total_users * 100), 2) if total_users > 0 else 0
            })

        # Top 5 profils (déjà triés par la requête)
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

        # Statistiques d'utilisation - utiliser Q() au lieu de list() pour éviter l'évaluation en mémoire
        usages = UserProfileUsage.objects.filter(
            Q(user__profile=profile) | Q(user__promotion__profile=profile, user__profile__isnull=True),
            user__is_active=True,
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

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def assign_to_user(self, request, pk=None):
        """
        Assigne ce profil à un utilisateur individuel.

        POST /api/core/profiles/{id}/assign_to_user/
        Body: {"user_id": 123}
        """
        from radius.services import ProfileAssignmentService

        profile = self.get_object()
        user_id = request.data.get('user_id')

        if not user_id:
            return Response(
                format_api_error('missing_user_id', 'L\'ID utilisateur est requis.'),
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise ResourceNotFoundError('Utilisateur non trouvé.')

        result = ProfileAssignmentService.assign_profile_to_user(
            user=user,
            profile=profile,
            assigned_by=request.user
        )

        if result['success']:
            return Response(format_api_success(result['message']))
        else:
            return Response(
                format_api_error('assignment_failed', result.get('error', 'Erreur inconnue')),
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def assign_to_promotion(self, request, pk=None):
        """
        Assigne ce profil à une promotion et synchronise tous ses utilisateurs.

        POST /api/core/profiles/{id}/assign_to_promotion/
        Body: {"promotion_id": 123}
        """
        from radius.services import ProfileAssignmentService

        profile = self.get_object()
        promotion_id = request.data.get('promotion_id')

        if not promotion_id:
            return Response(
                format_api_error('missing_promotion_id', 'L\'ID de promotion est requis.'),
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            promotion = Promotion.objects.get(pk=promotion_id)
        except Promotion.DoesNotExist:
            raise ResourceNotFoundError('Promotion non trouvée.')

        result = ProfileAssignmentService.assign_profile_to_promotion(
            promotion=promotion,
            profile=profile,
            assigned_by=request.user
        )

        return Response(format_api_success(
            result['message'],
            data={
                'synced_users': result.get('synced_users', 0),
                'errors': result.get('errors', [])
            }
        ))

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def remove_from_user(self, request, pk=None):
        """
        Retire ce profil d'un utilisateur (il utilisera le profil de sa promotion).

        POST /api/core/profiles/{id}/remove_from_user/
        Body: {"user_id": 123}
        """
        from radius.services import ProfileAssignmentService

        profile = self.get_object()
        user_id = request.data.get('user_id')

        if not user_id:
            return Response(
                format_api_error('missing_user_id', 'L\'ID utilisateur est requis.'),
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise ResourceNotFoundError('Utilisateur non trouvé.')

        if user.profile != profile:
            return Response(
                format_api_error('profile_mismatch', 'Cet utilisateur n\'a pas ce profil assigné.'),
                status=status.HTTP_400_BAD_REQUEST
            )

        result = ProfileAssignmentService.remove_profile_from_user(
            user=user,
            removed_by=request.user
        )

        if result['success']:
            return Response(format_api_success(result['message']))
        else:
            return Response(
                format_api_error('removal_failed', result.get('error', 'Erreur inconnue')),
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def sync_to_radius(self, request, pk=None):
        """
        Force la synchronisation de tous les utilisateurs de ce profil vers RADIUS.

        POST /api/core/profiles/{id}/sync_to_radius/
        """
        from radius.services import ProfileRadiusService

        profile = self.get_object()

        # Récupérer tous les utilisateurs avec ce profil
        direct_users = User.objects.filter(
            profile=profile,
            is_radius_activated=True
        )
        promotion_users = User.objects.filter(
            promotion__profile=profile,
            profile__isnull=True,
            is_radius_activated=True
        )

        all_users = list(direct_users) + list(promotion_users)
        synced = 0
        errors = []

        for user in all_users:
            try:
                ProfileRadiusService.sync_user_to_radius(user, profile)
                synced += 1
            except Exception as e:
                errors.append({'user': user.username, 'error': str(e)})

        return Response(format_api_success(
            f'{synced} utilisateurs synchronisés vers RADIUS.',
            data={
                'total': len(all_users),
                'synced': synced,
                'errors': errors
            }
        ))

    # =========================================================================
    # RADIUS Profile Group Sync Actions (Option C)
    # =========================================================================

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def enable_radius(self, request, pk=None):
        """
        Active la synchronisation RADIUS pour ce profil.
        Crée les entrées radgroupreply correspondantes.

        POST /api/core/profiles/{id}/enable_radius/

        Response:
        {
            "success": true,
            "message": "Profil 'Étudiant' activé dans RADIUS",
            "data": {
                "groupname": "profile_1_etudiant",
                "attributes": 4,
                "synced_at": "2024-01-15T10:30:00Z"
            }
        }
        """
        profile = self.get_object()

        if not profile.is_active:
            return Response(
                format_api_error(
                    'profile_inactive',
                    'Le profil doit être actif pour activer RADIUS.'
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        if profile.is_radius_enabled and profile.is_synced_to_radius:
            return Response(
                format_api_error(
                    'already_enabled',
                    f'Le profil est déjà activé dans RADIUS (groupe: {profile.radius_group_name}).'
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Activer et synchroniser
            profile.is_radius_enabled = True
            profile.save()  # Déclenche le signal post_save

            # Recharger pour obtenir les valeurs mises à jour
            profile.refresh_from_db()

            return Response(format_api_success(
                f"Profil '{profile.name}' activé dans RADIUS.",
                data={
                    'groupname': profile.radius_group_name,
                    'synced_at': profile.last_radius_sync.isoformat() if profile.last_radius_sync else None,
                    'status': profile.radius_sync_status
                }
            ))

        except Exception as e:
            return Response(
                format_api_error('sync_failed', f'Erreur de synchronisation: {str(e)}'),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def disable_radius(self, request, pk=None):
        """
        Désactive la synchronisation RADIUS pour ce profil.
        Supprime les entrées radgroupreply correspondantes.

        POST /api/core/profiles/{id}/disable_radius/

        Response:
        {
            "success": true,
            "message": "Profil 'Étudiant' désactivé de RADIUS",
            "data": {
                "removed_group": "profile_1_etudiant"
            }
        }
        """
        profile = self.get_object()

        if not profile.is_radius_enabled:
            return Response(
                format_api_error(
                    'already_disabled',
                    'Le profil n\'est pas activé dans RADIUS.'
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        old_group = profile.radius_group_name

        try:
            # Désactiver (le signal supprimera de radgroupreply)
            profile.is_radius_enabled = False
            profile.save()

            return Response(format_api_success(
                f"Profil '{profile.name}' désactivé de RADIUS.",
                data={
                    'removed_group': old_group
                }
            ))

        except Exception as e:
            return Response(
                format_api_error('disable_failed', f'Erreur: {str(e)}'),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def toggle_radius(self, request, pk=None):
        """
        Toggle la synchronisation RADIUS pour ce profil.

        POST /api/core/profiles/{id}/toggle_radius/

        Response:
        {
            "success": true,
            "message": "RADIUS activé/désactivé pour le profil 'Étudiant'",
            "data": {
                "is_radius_enabled": true/false,
                "radius_group_name": "profile_1_etudiant" | null,
                "status": "Synchronisé (profile_1_etudiant)" | "Sync RADIUS désactivée"
            }
        }
        """
        profile = self.get_object()

        if not profile.is_active:
            return Response(
                format_api_error(
                    'profile_inactive',
                    'Le profil doit être actif pour modifier le statut RADIUS.'
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Toggle
            profile.is_radius_enabled = not profile.is_radius_enabled
            profile.save()

            # Recharger pour obtenir les valeurs mises à jour
            profile.refresh_from_db()

            action = 'activé' if profile.is_radius_enabled else 'désactivé'

            return Response(format_api_success(
                f"RADIUS {action} pour le profil '{profile.name}'.",
                data={
                    'is_radius_enabled': profile.is_radius_enabled,
                    'radius_group_name': profile.radius_group_name,
                    'last_radius_sync': profile.last_radius_sync.isoformat() if profile.last_radius_sync else None,
                    'status': profile.radius_sync_status
                }
            ))

        except Exception as e:
            return Response(
                format_api_error('toggle_failed', f'Erreur: {str(e)}'),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def force_sync_radius(self, request, pk=None):
        """
        Force la resynchronisation du profil vers radgroupreply.
        Utile après une modification manuelle de la base RADIUS.

        POST /api/core/profiles/{id}/force_sync_radius/

        Response:
        {
            "success": true,
            "message": "Profil 'Étudiant' resynchronisé vers RADIUS",
            "data": {
                "groupname": "profile_1_etudiant",
                "reply_attributes": 4,
                "check_attributes": 0
            }
        }
        """
        profile = self.get_object()

        if not profile.can_sync_to_radius():
            return Response(
                format_api_error(
                    'cannot_sync',
                    'Le profil doit être actif et RADIUS activé pour synchroniser.'
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = profile.sync_to_radius()

            if result.get('success'):
                return Response(format_api_success(
                    f"Profil '{profile.name}' resynchronisé vers RADIUS.",
                    data=result
                ))
            else:
                return Response(
                    format_api_error('sync_failed', result.get('error', 'Erreur inconnue')),
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            return Response(
                format_api_error('sync_failed', f'Erreur: {str(e)}'),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], permission_classes=[IsAdmin])
    def radius_status(self, request, pk=None):
        """
        Retourne le statut de synchronisation RADIUS du profil.

        GET /api/core/profiles/{id}/radius_status/

        Response:
        {
            "profile_id": 1,
            "profile_name": "Étudiant",
            "is_active": true,
            "is_radius_enabled": true,
            "is_synced": true,
            "radius_group_name": "profile_1_etudiant",
            "last_sync": "2024-01-15T10:30:00Z",
            "status": "Synchronisé (profile_1_etudiant)",
            "can_sync": true
        }
        """
        profile = self.get_object()

        return Response({
            'profile_id': profile.id,
            'profile_name': profile.name,
            'is_active': profile.is_active,
            'is_radius_enabled': profile.is_radius_enabled,
            'is_synced': profile.is_synced_to_radius,
            'radius_group_name': profile.radius_group_name,
            'last_sync': profile.last_radius_sync.isoformat() if profile.last_radius_sync else None,
            'status': profile.radius_sync_status,
            'can_sync': profile.can_sync_to_radius()
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAdmin])
    def bulk_enable_radius(self, request):
        """
        Active RADIUS pour plusieurs profils en masse.

        POST /api/core/profiles/bulk_enable_radius/
        Body: {"profile_ids": [1, 2, 3]}

        Fix #29: Suivi détaillé de progression avec résultats par profil.
        Fix #10: Journalisation d'audit.

        Response:
        {
            "success": true,
            "message": "3 profils activés dans RADIUS",
            "data": {
                "enabled": 3,
                "skipped": 1,
                "failed": 0,
                "total": 4,
                "results": [
                    {"id": 1, "name": "Étudiant", "status": "enabled", "groupname": "profile_1_etudiant"},
                    {"id": 2, "name": "Premium", "status": "skipped", "reason": "already_enabled"},
                    {"id": 3, "name": "Inactif", "status": "skipped", "reason": "profile_inactive"}
                ],
                "errors": []
            }
        }
        """
        from .models import AdminAuditLog
        from .security import BulkOperationValidator

        # Fix #9: Validation stricte des entrées bulk
        validated, validation_errors = BulkOperationValidator.validate_bulk_request(
            request.data,
            id_field='profile_ids',
            max_size=100
        )

        if validation_errors:
            return Response(
                format_api_error('validation_error', 'Données invalides', {'errors': validation_errors}),
                status=status.HTTP_400_BAD_REQUEST
            )

        profile_ids = validated['profile_ids']

        if not profile_ids:
            return Response(
                format_api_error('missing_ids', 'La liste des IDs de profils est requise.'),
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fix #29: Résultats détaillés par profil
        results = []
        enabled = 0
        skipped = 0
        failed = 0

        # Récupérer tous les profils demandés
        profiles = Profile.objects.filter(id__in=profile_ids)
        found_ids = set(profiles.values_list('id', flat=True))

        # Marquer les IDs non trouvés (Fix #9: IDs déjà validés comme entiers)
        for pid in profile_ids:
            if pid not in found_ids:
                results.append({
                    'id': pid,
                    'name': None,
                    'status': 'failed',
                    'reason': 'not_found'
                })
                failed += 1

        for profile in profiles:
            try:
                if not profile.is_active:
                    results.append({
                        'id': profile.id,
                        'name': profile.name,
                        'status': 'skipped',
                        'reason': 'profile_inactive'
                    })
                    skipped += 1
                elif profile.is_radius_enabled:
                    results.append({
                        'id': profile.id,
                        'name': profile.name,
                        'status': 'skipped',
                        'reason': 'already_enabled',
                        'groupname': profile.radius_group_name
                    })
                    skipped += 1
                else:
                    profile.is_radius_enabled = True
                    profile.save()
                    profile.refresh_from_db()
                    results.append({
                        'id': profile.id,
                        'name': profile.name,
                        'status': 'enabled',
                        'groupname': profile.radius_group_name
                    })
                    enabled += 1

            except Exception as e:
                results.append({
                    'id': profile.id,
                    'name': profile.name,
                    'status': 'failed',
                    'reason': str(e)[:100]
                })
                failed += 1

        # Fix #10: Audit logging
        AdminAuditLog.log_action(
            admin_user=request.user,
            action_type='bulk_radius_enable',
            target=('Profile', None, f'{enabled} profils activés'),
            details={
                'profile_ids': profile_ids,
                'enabled': enabled,
                'skipped': skipped,
                'failed': failed
            },
            success=failed == 0,
            request=request
        )

        return Response(format_api_success(
            f'{enabled} profil(s) activé(s) dans RADIUS.',
            data={
                'enabled': enabled,
                'skipped': skipped,
                'failed': failed,
                'total': len(profile_ids),
                'results': results
            }
        ))

    @action(detail=False, methods=['post'], permission_classes=[IsAdmin])
    def bulk_disable_radius(self, request):
        """
        Désactive RADIUS pour plusieurs profils en masse.

        POST /api/core/profiles/bulk_disable_radius/
        Body: {"profile_ids": [1, 2, 3]}

        Fix #29: Suivi détaillé de progression avec résultats par profil.
        Fix #10: Journalisation d'audit.

        Response:
        {
            "success": true,
            "message": "3 profils désactivés de RADIUS",
            "data": {
                "disabled": 3,
                "skipped": 1,
                "failed": 0,
                "total": 4,
                "results": [...]
            }
        }
        """
        from .models import AdminAuditLog
        from .security import BulkOperationValidator

        # Fix #9: Validation stricte des entrées bulk
        validated, validation_errors = BulkOperationValidator.validate_bulk_request(
            request.data,
            id_field='profile_ids',
            max_size=100
        )

        if validation_errors:
            return Response(
                format_api_error('validation_error', 'Données invalides', {'errors': validation_errors}),
                status=status.HTTP_400_BAD_REQUEST
            )

        profile_ids = validated['profile_ids']

        if not profile_ids:
            return Response(
                format_api_error('missing_ids', 'La liste des IDs de profils est requise.'),
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fix #29: Résultats détaillés
        results = []
        disabled = 0
        skipped = 0
        failed = 0

        profiles = Profile.objects.filter(id__in=profile_ids)
        found_ids = set(profiles.values_list('id', flat=True))

        for pid in profile_ids:
            if pid not in found_ids:
                results.append({
                    'id': pid,
                    'name': None,
                    'status': 'failed',
                    'reason': 'not_found'
                })
                failed += 1

        for profile in profiles:
            try:
                if not profile.is_radius_enabled:
                    results.append({
                        'id': profile.id,
                        'name': profile.name,
                        'status': 'skipped',
                        'reason': 'already_disabled'
                    })
                    skipped += 1
                else:
                    old_groupname = profile.radius_group_name
                    profile.is_radius_enabled = False
                    profile.save()
                    results.append({
                        'id': profile.id,
                        'name': profile.name,
                        'status': 'disabled',
                        'removed_group': old_groupname
                    })
                    disabled += 1

            except Exception as e:
                results.append({
                    'id': profile.id,
                    'name': profile.name,
                    'status': 'failed',
                    'reason': str(e)[:100]
                })
                failed += 1

        # Fix #10: Audit logging
        AdminAuditLog.log_action(
            admin_user=request.user,
            action_type='bulk_radius_disable',
            target=('Profile', None, f'{disabled} profils désactivés'),
            details={
                'profile_ids': profile_ids,
                'disabled': disabled,
                'skipped': skipped,
                'failed': failed
            },
            success=failed == 0,
            request=request
        )

        return Response(format_api_success(
            f'{disabled} profil(s) désactivé(s) de RADIUS.',
            data={
                'disabled': disabled,
                'skipped': skipped,
                'failed': failed,
                'total': len(profile_ids),
                'results': results
            }
        ))


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
        Utilise le système de groupes RADIUS (radgroupreply) pour les attributs.
        """
        from radius.models import RadCheck, RadUserGroup
        from radius.services import RadiusProfileGroupService

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

                # 1. radcheck - Mot de passe en clair (SEULE entrée individuelle nécessaire)
                RadCheck.objects.update_or_create(
                    username=user.username,
                    attribute='Cleartext-Password',
                    defaults={
                        'op': ':=',
                        'value': user.cleartext_password,
                        'statut': True
                    }
                )

                # 2. radcheck - Simultaneous-Use (limite de connexions)
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

                # 3. radusergroup - Groupe de rôle (admin/user) avec priorité basse
                RadUserGroup.objects.update_or_create(
                    username=user.username,
                    groupname=user.role,
                    defaults={'priority': 10}  # Priorité basse pour le rôle
                )

                # 4. Assigner au groupe de profil via le service dédié
                # Le groupe de profil contient tous les attributs reply (bandwidth, timeouts, quota)
                if profile:
                    RadiusProfileGroupService.sync_user_profile_group(user)

                # Mettre à jour les statuts
                user.is_radius_activated = True
                user.is_radius_enabled = True
                user.save(update_fields=['is_radius_activated', 'is_radius_enabled'])

                # Calculer les valeurs pour la réponse
                if profile:
                    bandwidth_value = f"{profile.bandwidth_download}M/{profile.bandwidth_upload}M"
                    session_timeout = profile.session_timeout
                else:
                    bandwidth_value = '10M/10M'
                    session_timeout = 86400 if user.is_staff else 3600

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
                # nowait=False permet d'attendre plutôt que d'échouer immédiatement
                try:
                    voucher = Voucher.objects.select_for_update(nowait=False).get(code=code)
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

                # Vérifier qu'il reste des utilisations disponibles
                if voucher.used_count >= voucher.max_devices:
                    raise VoucherAlreadyUsedError(
                        detail='Ce voucher a atteint sa limite d\'utilisation.'
                    )

                # Utiliser le voucher avec incrément atomique via F()
                from django.db.models import F
                voucher.used_by = request.user
                voucher.used_at = now

                # Incrémenter de manière atomique et mettre à jour le statut
                Voucher.objects.filter(pk=voucher.pk).update(
                    used_count=F('used_count') + 1,
                    used_by=request.user,
                    used_at=now
                )

                # Recharger pour obtenir la nouvelle valeur
                voucher.refresh_from_db()

                # Mettre à jour le statut si limite atteinte
                if voucher.used_count >= voucher.max_devices:
                    voucher.status = 'used'
                    voucher.save(update_fields=['status'])

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
    """ViewSet for BlockedSite model with MikroTik DNS synchronization"""
    queryset = BlockedSite.objects.all()
    serializer_class = BlockedSiteSerializer
    permission_classes = [IsAdmin]

    def _sync_to_mikrotik(self, blocked_site, action='add'):
        """
        Synchronise un site bloqué avec MikroTik DNS.

        Args:
            blocked_site: Instance BlockedSite
            action: 'add', 'update', ou 'remove'
        """
        try:
            from mikrotik.dns_service import MikrotikDNSBlockingService
            service = MikrotikDNSBlockingService()

            if action == 'add':
                result = service.add_blocked_domain(blocked_site)
            elif action == 'update':
                result = service.update_blocked_domain(blocked_site)
            elif action == 'remove':
                result = service.remove_blocked_domain(blocked_site)
            else:
                result = {'success': False, 'error': f'Action inconnue: {action}'}

            return result
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur sync MikroTik pour {blocked_site.domain}: {str(e)}")
            blocked_site.mark_error(str(e))
            return {'success': False, 'error': str(e)}

    def perform_create(self, serializer):
        """Crée un site bloqué et le synchronise avec MikroTik"""
        instance = serializer.save()
        if instance.is_active and instance.type == 'blacklist':
            self._sync_to_mikrotik(instance, 'add')

    def perform_update(self, serializer):
        """Met à jour un site bloqué et synchronise avec MikroTik"""
        instance = serializer.save()
        if instance.is_active and instance.type == 'blacklist':
            if instance.mikrotik_id:
                self._sync_to_mikrotik(instance, 'update')
            else:
                self._sync_to_mikrotik(instance, 'add')
        elif not instance.is_active and instance.mikrotik_id:
            # Si désactivé, supprimer de MikroTik
            self._sync_to_mikrotik(instance, 'remove')

    def perform_destroy(self, instance):
        """Supprime un site bloqué et le retire de MikroTik"""
        if instance.mikrotik_id:
            self._sync_to_mikrotik(instance, 'remove')
        instance.delete()

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

    @action(detail=False, methods=['get'])
    def whitelist(self, request):
        """Get all whitelisted sites"""
        sites = BlockedSite.objects.filter(type='whitelist', is_active=True)
        serializer = self.get_serializer(sites, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Synchronise manuellement un site avec MikroTik"""
        site = self.get_object()

        if not site.is_active:
            return Response({
                'success': False,
                'error': 'Le site n\'est pas actif'
            }, status=status.HTTP_400_BAD_REQUEST)

        if site.type != 'blacklist':
            return Response({
                'success': False,
                'error': 'Seuls les sites en blacklist peuvent être synchronisés'
            }, status=status.HTTP_400_BAD_REQUEST)

        action = 'update' if site.mikrotik_id else 'add'
        result = self._sync_to_mikrotik(site, action)

        if result.get('success'):
            return Response({
                'success': True,
                'message': f'Site {site.domain} synchronisé avec succès',
                'mikrotik_id': site.mikrotik_id
            })
        else:
            return Response({
                'success': False,
                'error': result.get('error', 'Erreur inconnue')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def sync_all(self, request):
        """Synchronise tous les sites en attente avec MikroTik"""
        pending_sites = BlockedSite.objects.filter(
            sync_status__in=['pending', 'error'],
            is_active=True,
            type='blacklist'
        )

        results = {
            'total': pending_sites.count(),
            'success': 0,
            'failed': 0,
            'errors': []
        }

        for site in pending_sites:
            action = 'update' if site.mikrotik_id else 'add'
            result = self._sync_to_mikrotik(site, action)

            if result.get('success'):
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'domain': site.domain,
                    'error': result.get('error', 'Erreur inconnue')
                })

        return Response(results)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retourne les statistiques des sites bloqués"""
        return Response({
            'total': BlockedSite.objects.count(),
            'blacklist': BlockedSite.objects.filter(type='blacklist').count(),
            'whitelist': BlockedSite.objects.filter(type='whitelist').count(),
            'active': BlockedSite.objects.filter(is_active=True).count(),
            'synced': BlockedSite.objects.filter(sync_status='synced').count(),
            'pending': BlockedSite.objects.filter(sync_status='pending').count(),
            'error': BlockedSite.objects.filter(sync_status='error').count(),
        })


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
        """
        promotion = self.get_object()
        # Optimiser les requêtes avec select_related
        users_queryset = promotion.users.filter(is_active=True).select_related(
            'promotion', 'profile'
        )

        users_data = []
        for user in users_queryset:
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
                'name': promotion.name,
                'is_active': promotion.is_active
            },
            'users': users_data,
            'count': len(users_data)
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def deactivate(self, request, pk=None):
        """
        Désactive une promotion et désactive l'accès RADIUS des utilisateurs.

        Workflow RADIUS conforme FreeRADIUS:
        - Désactive le mot de passe dans radcheck (statut=False)
        - Retire les utilisateurs de leurs groupes de profil (radusergroup)
        - NE TOUCHE PAS à radreply (non utilisé pour les profils)

        Les utilisateurs n'auront plus accès à Internet mais gardent leurs credentials.
        """
        from radius.services import ProfileRadiusService, RadiusProfileGroupService

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

                # Récupérer TOUS les utilisateurs RADIUS activés de la promotion
                users_to_disable = promotion.users.filter(
                    is_active=True,
                    is_radius_activated=True
                )
                disabled_count = 0
                failed_count = 0
                errors = []

                for user in users_to_disable:
                    try:
                        # Utiliser select_for_update pour éviter les race conditions
                        user = User.objects.select_for_update().get(id=user.id)

                        # Utiliser le service RADIUS pour désactiver proprement
                        result = ProfileRadiusService.deactivate_user_radius(
                            user,
                            reason='promotion_deactivated',
                            deactivated_by=request.user
                        )

                        if result.get('success'):
                            # Retirer des groupes de profil
                            RadiusProfileGroupService.remove_user_from_profile_groups(user.username)
                            disabled_count += 1
                        else:
                            failed_count += 1
                            errors.append({
                                'username': user.username,
                                'error': result.get('error', 'Erreur inconnue')
                            })

                    except Exception as e:
                        failed_count += 1
                        errors.append({'username': user.username, 'error': str(e)})

                return Response(format_api_success(
                    f'Promotion "{promotion.name}" désactivée. {disabled_count} utilisateur(s) désactivé(s) dans RADIUS.',
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

        Workflow RADIUS conforme FreeRADIUS:
        1. S'assure que le groupe du profil existe dans radgroupreply/radgroupcheck
        2. Crée les credentials dans radcheck pour chaque utilisateur
        3. Assigne chaque utilisateur à son groupe de profil via radusergroup
        4. NE TOUCHE PAS à radreply (les attributs sont dans radgroupreply)

        Les attributs RADIUS (bandwidth, timeout, quota) sont centralisés dans
        radgroupreply et appliqués via l'association radusergroup.
        """
        from radius.services import ProfileRadiusService, RadiusProfileGroupService

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

                # Vérifier que la promotion a un profil assigné
                if not promotion.profile:
                    return Response(
                        format_api_error(
                            'no_profile',
                            f'La promotion "{promotion.name}" n\'a pas de profil assigné.'
                        ),
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # 1. S'assurer que le groupe du profil existe dans RADIUS
                profile = promotion.profile
                if profile.is_active:
                    group_result = RadiusProfileGroupService.sync_profile_to_radius_group(profile)
                    if not group_result.get('success'):
                        return Response(
                            format_api_error(
                                'profile_sync_failed',
                                f'Échec de synchronisation du profil "{profile.name}" vers RADIUS.'
                            ),
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )

                # Activer la promotion
                promotion.is_active = True
                promotion.save(update_fields=['is_active'])

                # Récupérer TOUS les utilisateurs actifs de la promotion
                users_to_enable = promotion.users.filter(is_active=True)
                enabled_count = 0
                reactivated_count = 0
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

                        # Utiliser le service RADIUS pour activer proprement
                        if user.is_radius_activated:
                            # Déjà activé, juste réactiver si désactivé
                            if not user.is_radius_enabled:
                                result = ProfileRadiusService.reactivate_user_radius(
                                    user,
                                    reactivated_by=request.user
                                )
                                if result.get('success'):
                                    # S'assurer que l'utilisateur est dans le bon groupe
                                    RadiusProfileGroupService.sync_user_profile_group(user)
                                    reactivated_count += 1
                                else:
                                    failed_count += 1
                                    errors.append({
                                        'username': user.username,
                                        'error': result.get('error', 'Erreur réactivation')
                                    })
                            else:
                                # Déjà activé et actif, sync le groupe
                                RadiusProfileGroupService.sync_user_profile_group(user)
                                enabled_count += 1
                        else:
                            # Première activation
                            result = ProfileRadiusService.activate_user_radius(
                                user,
                                activated_by=request.user
                            )
                            if result.get('success'):
                                enabled_count += 1
                            else:
                                failed_count += 1
                                errors.append({
                                    'username': user.username,
                                    'error': result.get('error', 'Erreur activation')
                                })

                    except Exception as e:
                        failed_count += 1
                        errors.append({'username': user.username, 'error': str(e)})

                total_success = enabled_count + reactivated_count
                message = f'Promotion "{promotion.name}" activée.'
                if enabled_count > 0:
                    message += f' {enabled_count} utilisateur(s) activé(s).'
                if reactivated_count > 0:
                    message += f' {reactivated_count} utilisateur(s) réactivé(s).'

                return Response(format_api_success(
                    message,
                    {
                        'promotion': {
                            'id': promotion.id,
                            'name': promotion.name,
                            'is_active': promotion.is_active,
                            'profile': profile.name
                        },
                        'profile_group': RadiusProfileGroupService.get_group_name(profile),
                        'users_enabled': enabled_count,
                        'users_reactivated': reactivated_count,
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
    def toggle_status(self, request, pk=None):
        """
        Bascule le statut actif/inactif d'une promotion.
        Change simplement is_active sans affecter les utilisateurs RADIUS.
        """
        try:
            promotion = self.get_object()
            promotion.is_active = not promotion.is_active
            promotion.save(update_fields=['is_active'])

            # Retourner la promotion complète sérialisée
            serializer = self.get_serializer(promotion)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                format_api_error('toggle_failed', f'Erreur: {str(e)}'),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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

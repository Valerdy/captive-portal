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
        """
        List all RADIUS users.
        Optimisé pour éviter les N+1 queries en utilisant des dictionnaires de lookup.
        """
        from rest_framework.pagination import PageNumberPagination

        # Récupérer tous les usernames uniques
        usernames = list(RadCheck.objects.values_list('username', flat=True).distinct())

        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = 50
        paginator.page_size_query_param = 'page_size'
        paginator.max_page_size = 200

        # Paginer les usernames
        page_usernames = paginator.paginate_queryset(usernames, request)

        if not page_usernames:
            return paginator.get_paginated_response([])

        # Créer des dictionnaires de lookup pour éviter les N+1 queries
        # Une seule requête par table au lieu de N requêtes

        # RadCheck passwords (filtrés par les usernames de la page)
        password_checks = {
            rc.username: rc for rc in
            RadCheck.objects.filter(
                username__in=page_usernames,
                attribute='Cleartext-Password'
            )
        }

        # Session timeouts
        timeout_replies = {
            rr.username: rr for rr in
            RadReply.objects.filter(
                username__in=page_usernames,
                attribute='Session-Timeout'
            )
        }

        # Bandwidth limits
        bandwidth_replies = {
            rr.username: rr for rr in
            RadReply.objects.filter(
                username__in=page_usernames,
                attribute='Mikrotik-Rate-Limit'
            )
        }

        # User groups
        user_groups = {
            rug.username: rug for rug in
            RadUserGroup.objects.filter(username__in=page_usernames)
        }

        # Statuts des utilisateurs
        statut_checks = {
            rc.username: rc for rc in
            RadCheck.objects.filter(
                username__in=page_usernames,
                attribute='Cleartext-Password'
            )
        }

        # Construire la réponse en utilisant les dictionnaires
        users_data = []
        for username in page_usernames:
            timeout_reply = timeout_replies.get(username)
            bandwidth_reply = bandwidth_replies.get(username)
            group = user_groups.get(username)
            statut_check = statut_checks.get(username)

            user_data = {
                'username': username,
                'groupname': group.groupname if group else 'user',
                'session_timeout': int(timeout_reply.value) if timeout_reply else 3600,
                'bandwidth_limit': bandwidth_reply.value if bandwidth_reply else '',
                'is_enabled': statut_check.statut if statut_check else False
            }
            users_data.append(user_data)

        return paginator.get_paginated_response(users_data)

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
        """
        Get all users in a specific group.
        Optimisé pour éviter les N+1 queries.
        """
        from rest_framework.pagination import PageNumberPagination

        groupname = request.query_params.get('groupname', 'user')
        usernames = list(RadUserGroup.objects.filter(groupname=groupname).values_list('username', flat=True))

        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = 50
        paginator.page_size_query_param = 'page_size'
        paginator.max_page_size = 200

        page_usernames = paginator.paginate_queryset(usernames, request)

        if not page_usernames:
            return paginator.get_paginated_response([])

        # Lookup dictionnaires pour éviter N+1 queries
        timeout_replies = {
            rr.username: rr for rr in
            RadReply.objects.filter(
                username__in=page_usernames,
                attribute='Session-Timeout'
            )
        }

        statut_checks = {
            rc.username: rc for rc in
            RadCheck.objects.filter(
                username__in=page_usernames,
                attribute='Cleartext-Password'
            )
        }

        users_data = []
        for username in page_usernames:
            timeout_reply = timeout_replies.get(username)
            statut_check = statut_checks.get(username)

            user_data = {
                'username': username,
                'groupname': groupname,
                'session_timeout': int(timeout_reply.value) if timeout_reply else 3600,
                'is_enabled': statut_check.statut if statut_check else False
            }
            users_data.append(user_data)

        return paginator.get_paginated_response(users_data)


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


# ============================================================================
# MikroTik Integration ViewSet
# ============================================================================

class MikrotikIntegrationViewSet(viewsets.ViewSet):
    """
    ViewSet pour l'intégration MikroTik.
    Permet de récupérer et synchroniser les profils Hotspot.
    """
    permission_classes = [permissions.IsAdminUser]

    @action(detail=False, methods=['get'])
    def hotspot_profiles(self, request):
        """
        Récupère la liste des profils Hotspot depuis MikroTik.

        GET /api/radius/mikrotik/hotspot_profiles/
        """
        from .services import MikrotikProfileService

        try:
            profiles = MikrotikProfileService.get_hotspot_profiles()
            return Response({
                'success': True,
                'profiles': profiles
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    @action(detail=False, methods=['get'])
    def default_profile(self, request):
        """
        Récupère le profil par défaut du Hotspot MikroTik.

        GET /api/radius/mikrotik/default_profile/
        """
        from .services import MikrotikProfileService

        try:
            profile = MikrotikProfileService.get_default_profile()
            if profile:
                # Mapper vers le format Django
                django_mapping = MikrotikProfileService.map_mikrotik_to_django_profile(profile)
                return Response({
                    'success': True,
                    'mikrotik_profile': profile,
                    'django_mapping': django_mapping
                })
            else:
                return Response({
                    'success': False,
                    'error': 'Aucun profil par défaut trouvé'
                }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    @action(detail=False, methods=['post'])
    def import_profile(self, request):
        """
        Importe un profil MikroTik vers Django.

        POST /api/radius/mikrotik/import_profile/
        Body: {"mikrotik_profile_name": "default"}
        """
        from .services import MikrotikProfileService
        from core.models import Profile

        profile_name = request.data.get('mikrotik_profile_name', 'default')

        try:
            # Récupérer les profils MikroTik
            profiles = MikrotikProfileService.get_hotspot_profiles()
            mikrotik_profile = next(
                (p for p in profiles if p.get('name') == profile_name),
                None
            )

            if not mikrotik_profile:
                return Response({
                    'success': False,
                    'error': f'Profil "{profile_name}" non trouvé dans MikroTik'
                }, status=status.HTTP_404_NOT_FOUND)

            # Mapper vers Django
            django_data = MikrotikProfileService.map_mikrotik_to_django_profile(mikrotik_profile)

            # Vérifier si un profil avec ce nom existe déjà
            existing = Profile.objects.filter(name=django_data['name']).first()
            if existing:
                # Mettre à jour
                for key, value in django_data.items():
                    setattr(existing, key, value)
                existing.save()
                message = f'Profil "{django_data["name"]}" mis à jour depuis MikroTik'
                profile = existing
            else:
                # Créer
                profile = Profile.objects.create(
                    created_by=request.user,
                    **django_data
                )
                message = f'Profil "{django_data["name"]}" importé depuis MikroTik'

            return Response({
                'success': True,
                'message': message,
                'profile': {
                    'id': profile.id,
                    'name': profile.name,
                    'bandwidth_upload': profile.bandwidth_upload,
                    'bandwidth_download': profile.bandwidth_download,
                    'session_timeout': profile.session_timeout,
                    'idle_timeout': profile.idle_timeout
                }
            })

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def connection_test(self, request):
        """
        Teste la connexion avec l'agent MikroTik.

        GET /api/radius/mikrotik/connection_test/
        """
        import requests

        try:
            response = requests.get(
                'http://localhost:3001/health',
                timeout=5
            )
            response.raise_for_status()

            return Response({
                'success': True,
                'message': 'Connexion MikroTik agent réussie',
                'agent_status': response.json()
            })
        except requests.ConnectionError:
            return Response({
                'success': False,
                'error': 'Impossible de contacter l\'agent MikroTik. Vérifiez qu\'il est démarré.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# RADIUS Sync ViewSet - API pour la synchronisation depuis l'interface
# ============================================================================

class RadiusSyncViewSet(viewsets.ViewSet):
    """
    ViewSet pour la synchronisation RADIUS depuis l'interface web.

    Endpoints:
    - POST /api/radius/sync/profile/{id}/activate/  → Activer un profil dans RADIUS
    - POST /api/radius/sync/profile/{id}/sync/      → Synchroniser un profil
    - POST /api/radius/sync/all-profiles/           → Synchroniser tous les profils
    - POST /api/radius/sync/all-users/              → Synchroniser tous les utilisateurs
    - POST /api/radius/sync/full/                   → Synchronisation complète
    - GET  /api/radius/sync/status/                 → Statut de synchronisation
    """
    permission_classes = [permissions.IsAdminUser]

    @action(detail=False, methods=['post'], url_path='profile/(?P<profile_id>[^/.]+)/activate')
    def activate_profile(self, request, profile_id=None):
        """
        Active un profil dans RADIUS et le synchronise.

        POST /api/radius/sync/profile/{profile_id}/activate/

        C'est l'endpoint principal appelé par le bouton "Activer dans RADIUS".
        """
        from core.services.radius_sync_service import RadiusSyncService

        try:
            profile_id = int(profile_id)
        except (ValueError, TypeError):
            return Response({
                'success': False,
                'error': 'ID de profil invalide'
            }, status=status.HTTP_400_BAD_REQUEST)

        result = RadiusSyncService.activate_profile_in_radius(profile_id)

        if result['success']:
            return Response(result)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='profile/(?P<profile_id>[^/.]+)/deactivate')
    def deactivate_profile(self, request, profile_id=None):
        """
        Désactive un profil dans RADIUS.

        POST /api/radius/sync/profile/{profile_id}/deactivate/
        """
        from core.services.radius_sync_service import RadiusSyncService

        try:
            profile_id = int(profile_id)
        except (ValueError, TypeError):
            return Response({
                'success': False,
                'error': 'ID de profil invalide'
            }, status=status.HTTP_400_BAD_REQUEST)

        result = RadiusSyncService.deactivate_profile_in_radius(profile_id)

        if result['success']:
            return Response(result)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='profile/(?P<profile_id>[^/.]+)/sync')
    def sync_profile(self, request, profile_id=None):
        """
        Synchronise un profil spécifique vers RADIUS (sans changer is_radius_enabled).

        POST /api/radius/sync/profile/{profile_id}/sync/
        """
        from core.services.radius_sync_service import RadiusSyncService

        try:
            profile_id = int(profile_id)
        except (ValueError, TypeError):
            return Response({
                'success': False,
                'error': 'ID de profil invalide'
            }, status=status.HTTP_400_BAD_REQUEST)

        result = RadiusSyncService.sync_profile(profile_id)

        if result['success']:
            return Response(result)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='all-profiles')
    def sync_all_profiles(self, request):
        """
        Synchronise tous les profils actifs vers RADIUS.

        POST /api/radius/sync/all-profiles/

        Équivalent à: python manage.py sync_radius_groups --profiles-only
        """
        from core.services.radius_sync_service import RadiusSyncService

        result = RadiusSyncService.sync_all_profiles()
        return Response(result)

    @action(detail=False, methods=['post'], url_path='all-users')
    def sync_all_users(self, request):
        """
        Synchronise tous les utilisateurs vers leurs groupes RADIUS.

        POST /api/radius/sync/all-users/

        Équivalent à: python manage.py sync_radius_groups --users-only
        """
        from core.services.radius_sync_service import RadiusSyncService

        result = RadiusSyncService.sync_all_users()
        return Response(result)

    @action(detail=False, methods=['post'], url_path='full')
    def sync_full(self, request):
        """
        Synchronisation complète: tous les profils + tous les utilisateurs.

        POST /api/radius/sync/full/

        Équivalent à: python manage.py sync_radius_groups
        """
        from core.services.radius_sync_service import RadiusSyncService

        result = RadiusSyncService.sync_all()
        return Response(result)

    @action(detail=False, methods=['get'], url_path='status')
    def sync_status(self, request):
        """
        Retourne le statut global de synchronisation RADIUS.

        GET /api/radius/sync/status/
        """
        from core.services.radius_sync_service import RadiusSyncService

        result = RadiusSyncService.get_sync_status()
        return Response(result)

    @action(detail=False, methods=['post'], url_path='user/(?P<user_id>[^/.]+)/sync')
    def sync_user(self, request, user_id=None):
        """
        Synchronise un utilisateur spécifique vers RADIUS.

        POST /api/radius/sync/user/{user_id}/sync/
        """
        from core.services.radius_sync_service import RadiusSyncService

        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            return Response({
                'success': False,
                'error': 'ID utilisateur invalide'
            }, status=status.HTTP_400_BAD_REQUEST)

        result = RadiusSyncService.sync_user(user_id)

        if result['success']:
            return Response(result)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='promotion/(?P<promotion_id>[^/.]+)/sync')
    def sync_promotion(self, request, promotion_id=None):
        """
        Synchronise tous les utilisateurs d'une promotion.

        POST /api/radius/sync/promotion/{promotion_id}/sync/
        """
        from core.services.radius_sync_service import RadiusSyncService

        try:
            promotion_id = int(promotion_id)
        except (ValueError, TypeError):
            return Response({
                'success': False,
                'error': 'ID promotion invalide'
            }, status=status.HTTP_400_BAD_REQUEST)

        result = RadiusSyncService.sync_promotion(promotion_id)

        if result['success']:
            return Response(result)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from .serializers import UserSerializer
from .models import Session, Device, User, Promotion
from .permissions import IsAdmin
from .decorators import rate_limit
from .utils import set_jwt_cookies, clear_jwt_cookies, generate_secure_password

# Import FreeRADIUS models for user creation
from radius.models import RadCheck, RadReply, RadUserGroup

# Try to import psutil for system metrics
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


@api_view(['POST'])
@permission_classes([AllowAny])
@rate_limit(key_prefix='register', rate='3/h', method='POST', block_duration=300)
def register(request):
    """
    User registration endpoint - allows direct registration.
    Users can register freely but must be activated by admin for RADIUS access.

    Required fields: first_name, last_name, promotion, matricule, password, password2
    Optional fields: username, email
    """
    # Extraire les données requises
    first_name = request.data.get('first_name', '').strip()
    last_name = request.data.get('last_name', '').strip()
    promotion_id = request.data.get('promotion') or request.data.get('promotion_id')
    promotion_name = request.data.get('promotion_name') or request.data.get('promotion_label')
    matricule = request.data.get('matricule', '').strip()
    password = request.data.get('password')
    password2 = request.data.get('password2')
    username = request.data.get('username', '').strip()
    email = request.data.get('email', '').strip()

    # Validation des champs requis
    if not all([first_name, last_name, matricule, password, password2]) or not (promotion_id or promotion_name):
        return Response({
            'error': 'Tous les champs sont requis',
            'detail': 'Veuillez remplir tous les champs: Nom, Prénom, Promotion, Matricule, Mot de passe'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Vérifier que les mots de passe correspondent
    if password != password2:
        return Response({
            'error': 'Les mots de passe ne correspondent pas',
            'detail': 'Le mot de passe et la confirmation doivent être identiques'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Générer username si non fourni (basé sur le matricule)
        if not username:
            username = matricule
            # Si le username existe déjà, ajouter un suffixe numérique
            if User.objects.filter(username=username).exists():
                counter = 1
                original_username = username
                while User.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1
                print(f"ℹ️  Username collision detected for '{original_username}' - using '{username}' instead")
        else:
            # Si l'utilisateur a fourni un username, vérifier qu'il est unique
            if User.objects.filter(username=username).exists():
                return Response({
                    'error': 'Nom d\'utilisateur déjà utilisé',
                    'detail': f'Le nom d\'utilisateur "{username}" est déjà pris. Veuillez en choisir un autre.'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Générer email si non fourni
        if not email:
            email = f"{matricule}@student.ucac-icam.com"
            # Si l'email existe déjà, ajouter un suffixe numérique
            if User.objects.filter(email=email).exists():
                counter = 1
                base_email = matricule
                while User.objects.filter(email=email).exists():
                    email = f"{base_email}{counter}@student.ucac-icam.com"
                    counter += 1
                print(f"ℹ️  Email collision detected - using '{email}' instead")

        # Valider le mot de passe avec les validateurs Django
        try:
            validate_password(password)
        except Exception as e:
            return Response({
                'error': 'Mot de passe invalide',
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        # Résoudre la promotion : priorise promotion_id, sinon crée/recupère par nom
        promotion_obj = None
        if promotion_id:
            try:
                promotion_obj = Promotion.objects.get(id=promotion_id)
            except Promotion.DoesNotExist:
                return Response({
                    'error': 'Promotion introuvable',
                    'detail': f'Promotion avec id={promotion_id} inexistante'
                }, status=status.HTTP_400_BAD_REQUEST)
        elif promotion_name:
            promotion_obj, _ = Promotion.objects.get_or_create(name=promotion_name.strip(), defaults={'is_active': True})

        # Utiliser une transaction pour garantir la cohérence
        with transaction.atomic():
            # Créer l'utilisateur directement
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,  # Stocké hashé par Django
                first_name=first_name,
                last_name=last_name,
                promotion=promotion_obj,
                matricule=matricule,
                is_active=True,
                # NE PAS activer dans RADIUS - l'admin doit le faire manuellement
                is_radius_activated=False
            )

            # STOCKAGE EN CLAIR pour activation RADIUS ultérieure
            # ATTENTION: Risque de sécurité si la base de données est compromise
            user.cleartext_password = password
            user.save()

            # NOTE: Les entrées FreeRADIUS (radcheck, radreply, radusergroup)
            # seront créées UNIQUEMENT lors de l'activation par l'administrateur
            # via l'endpoint /api/core/admin/users/activate/

            # Générer les tokens JWT
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # Create response
            response = Response({
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'promotion': user.promotion.id if user.promotion else None,
                    'promotion_name': user.promotion.name if user.promotion else None,
                    'matricule': user.matricule,
                    'role': user.role,
                    'is_radius_activated': user.is_radius_activated
                },
                'tokens': {
                    'refresh': refresh_token,
                    'access': access_token,
                },
                'message': 'Inscription réussie ! Votre compte doit être activé par un administrateur pour accéder au portail captif.',
                'auth_method': 'cookie',  # Indicate that cookies are being used
                'activation_pending': True,
                'warning': 'Votre compte n\'est pas encore activé dans RADIUS. Contactez un administrateur.'
            }, status=status.HTTP_201_CREATED)

            # Set tokens in secure HttpOnly cookies
            set_jwt_cookies(response, access_token, refresh_token)

            return response

    except Exception as e:
        return Response({
            'error': 'Erreur lors de l\'inscription',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
@rate_limit(key_prefix='login', rate='5/m', method='POST', block_duration=600)
def login(request):
    """
    User login endpoint
    """
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response(
            {'error': 'Please provide both username and password'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(username=username, password=password)

    if user is None:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        return Response(
            {'error': 'User account is disabled'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Generate tokens
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    # Create response
    response = Response({
        'user': UserSerializer(user).data,
        'tokens': {
            'refresh': refresh_token,
            'access': access_token,
        },
        'message': 'Login successful',
        'auth_method': 'cookie'  # Indicate that cookies are being used
    })

    # Set tokens in secure HttpOnly cookies
    set_jwt_cookies(response, access_token, refresh_token)

    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    User logout endpoint - blacklist the refresh token and clear cookies
    """
    try:
        # Try to get refresh token from request body or cookies
        refresh_token = request.data.get('refresh_token') or request.COOKIES.get('refresh_token')

        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()

        # Create response
        response = Response(
            {'message': 'Logout successful'},
            status=status.HTTP_200_OK
        )

        # Clear JWT cookies
        clear_jwt_cookies(response)

        return response
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Get current user profile
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    Update current user profile
    """
    serializer = UserSerializer(
        request.user,
        data=request.data,
        partial=request.method == 'PATCH'
    )

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@rate_limit(key_prefix='change_password', rate='10/h', method='POST', block_duration=300)
def change_password(request):
    """
    Change user password endpoint
    """
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')

    if not all([current_password, new_password, confirm_password]):
        return Response(
            {'error': 'All password fields are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Verify current password
    if not request.user.check_password(current_password):
        return Response(
            {'error': 'Current password is incorrect'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Verify new password matches confirmation
    if new_password != confirm_password:
        return Response(
            {'error': 'New passwords do not match'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check password strength (minimum 8 characters)
    if len(new_password) < 8:
        return Response(
            {'error': 'Password must be at least 8 characters long'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Change password
    request.user.set_password(new_password)
    request.user.save()

    return Response(
        {'message': 'Password changed successfully'},
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def monitoring_metrics(request):
    """
    Get real-time monitoring metrics (CPU, RAM, bandwidth, active connections)
    Admin only
    """
    try:
        # Get system metrics
        if PSUTIL_AVAILABLE:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
        else:
            # Fallback values if psutil is not installed
            cpu_usage = 0
            memory_usage = 0

        # Get active connections
        active_sessions = Session.objects.filter(status='active').count()
        active_devices = Device.objects.filter(is_active=True).count()

        # Calculate current bandwidth (last minute)
        one_minute_ago = timezone.now() - timedelta(minutes=1)
        recent_sessions = Session.objects.filter(
            updated_at__gte=one_minute_ago
        )

        # Total bandwidth in MB/s (approx)
        total_bytes = sum(
            (s.bytes_in + s.bytes_out) for s in recent_sessions
        )
        bandwidth_mbps = round((total_bytes / (1024 * 1024)) / 60, 2)  # MB/s

        # Get recent activity (last 10 sessions)
        recent_activity = []
        latest_sessions = Session.objects.select_related('user').order_by('-updated_at')[:10]

        for session in latest_sessions:
            recent_activity.append({
                'time': session.updated_at.strftime('%H:%M:%S'),
                'user': session.user.username,
                'action': 'Active' if session.status == 'active' else session.status.capitalize(),
                'ip': session.ip_address
            })

        return Response({
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'bandwidth': bandwidth_mbps,
            'active_connections': active_sessions,
            'active_devices': active_devices,
            'recent_activity': recent_activity,
            'psutil_available': PSUTIL_AVAILABLE,
            'timestamp': timezone.now().isoformat()
        })

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
@rate_limit(key_prefix='activate_radius', rate='20/h', method='POST', block_duration=60)
def activate_users_radius(request):
    """
    Admin endpoint to activate users in RADIUS.
    Creates entries in radcheck, radreply, and radusergroup for selected users.

    Request body:
        {
            "user_ids": [1, 2, 3, ...]
        }

    Response:
        {
            "success": true,
            "activated_users": [
                {
                    "id": 1,
                    "username": "jdupont",
                    "email": "jdupont@example.com",
                    "radius_password": "kT@9pL#mXq$1RvZ",
                    "message": "Utilisateur activé dans RADIUS"
                },
                ...
            ],
            "failed_users": [
                {
                    "id": 4,
                    "username": "jsmith",
                    "error": "Utilisateur déjà activé"
                },
                ...
            ]
        }
    """
    user_ids = request.data.get('user_ids', [])

    if not user_ids or not isinstance(user_ids, list):
        return Response({
            'error': 'user_ids requis',
            'detail': 'Veuillez fournir une liste d\'IDs d\'utilisateurs à activer'
        }, status=status.HTTP_400_BAD_REQUEST)

    activated_users = []
    failed_users = []

    for user_id in user_ids:
        try:
            with transaction.atomic():
                # Récupérer l'utilisateur
                user = User.objects.select_for_update().get(id=user_id)

                # Vérifier si l'utilisateur est déjà activé
                if user.is_radius_activated:
                    failed_users.append({
                        'id': user.id,
                        'username': user.username,
                        'error': 'Utilisateur déjà activé dans RADIUS'
                    })
                    continue

                # Vérifier que le mot de passe en clair est disponible
                if not user.cleartext_password:
                    failed_users.append({
                        'id': user.id,
                        'username': user.username,
                        'error': 'Mot de passe en clair non disponible (utilisateur créé avant cette fonctionnalité)'
                    })
                    continue

                # Utiliser le mot de passe en clair stocké lors de l'inscription
                radius_password = user.cleartext_password

                # 1. Créer l'entrée dans radcheck (mot de passe en clair pour FreeRADIUS)
                RadCheck.objects.update_or_create(
                    username=user.username,
                    attribute='Cleartext-Password',
                    defaults={
                        'op': ':=',
                        'value': radius_password,
                        'statut': True
                    }
                )

                # 2. Définir le timeout de session basé sur le rôle
                session_timeout = 86400 if user.role == 'admin' else 3600
                RadReply.objects.update_or_create(
                    username=user.username,
                    attribute='Session-Timeout',
                    defaults={
                        'op': '=',
                        'value': str(session_timeout)
                    }
                )

                # 3. Ajouter la limite de bande passante par défaut (10Mbps)
                RadReply.objects.update_or_create(
                    username=user.username,
                    attribute='Mikrotik-Rate-Limit',
                    defaults={
                        'op': '=',
                        'value': '10M/10M'
                    }
                )

                # 4. Assigner au groupe utilisateur
                RadUserGroup.objects.update_or_create(
                    username=user.username,
                    groupname=user.role,
                    defaults={'priority': 0}
                )

                # 5. Marquer l'utilisateur comme activé dans RADIUS
                user.is_radius_activated = True
                user.is_radius_enabled = True  # Activé par défaut
                user.save()

                # Ajouter aux utilisateurs activés avec succès
                activated_users.append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'promotion': user.promotion.name if user.promotion else None,
                    'matricule': user.matricule,
                    'radius_password': radius_password,
                    'session_timeout': f'{session_timeout//3600}h',
                    'bandwidth_limit': '10M/10M',
                    'message': 'Utilisateur activé dans RADIUS avec succès'
                })

        except User.DoesNotExist:
            failed_users.append({
                'id': user_id,
                'error': 'Utilisateur introuvable'
            })
        except Exception as e:
            failed_users.append({
                'id': user_id,
                'error': str(e)
            })

    return Response({
        'success': True,
        'message': f'{len(activated_users)} utilisateur(s) activé(s) dans RADIUS',
        'activated_users': activated_users,
        'failed_users': failed_users,
        'summary': {
            'total_requested': len(user_ids),
            'activated': len(activated_users),
            'failed': len(failed_users)
        },
        'important_note': 'Les utilisateurs peuvent désormais se connecter au WiFi avec le même mot de passe que pour l\'interface web.'
    }, status=status.HTTP_200_OK)

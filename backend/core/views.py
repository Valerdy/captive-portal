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
from .serializers import UserSerializer, AdminUserCreationSerializer
from .models import Session, Device, User
from .permissions import IsAdmin
from .decorators import rate_limit
from .utils import set_jwt_cookies, clear_jwt_cookies

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
    User registration endpoint with pre-registration validation.
    Only allows registration if user was pre-registered by an administrator.

    Required fields: first_name, last_name, promotion, matricule, password, password2
    """
    # Extraire les données requises
    first_name = request.data.get('first_name', '').strip()
    last_name = request.data.get('last_name', '').strip()
    promotion = request.data.get('promotion', '').strip()
    matricule = request.data.get('matricule', '').strip()
    password = request.data.get('password')
    password2 = request.data.get('password2')

    # Validation des champs requis
    if not all([first_name, last_name, promotion, matricule, password, password2]):
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
        # Rechercher un utilisateur pré-enregistré correspondant
        pre_registered_user = User.objects.filter(
            first_name__iexact=first_name,
            last_name__iexact=last_name,
            promotion__iexact=promotion,
            matricule__iexact=matricule,
            is_pre_registered=True
        ).first()

        # Si aucun utilisateur pré-enregistré trouvé
        if not pre_registered_user:
            return Response({
                'error': 'Inscription non autorisée',
                'detail': 'Aucun compte pré-enregistré ne correspond à vos informations. Veuillez contacter l\'administrateur.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Vérifier si l'utilisateur a déjà complété son inscription
        if pre_registered_user.registration_completed:
            return Response({
                'error': 'Inscription déjà complétée',
                'detail': 'Ce compte a déjà été activé. Utilisez la page de connexion pour vous connecter.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Valider le mot de passe avec les validateurs Django
        try:
            validate_password(password, user=pre_registered_user)
        except Exception as e:
            return Response({
                'error': 'Mot de passe invalide',
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        # Utiliser une transaction pour garantir la cohérence
        with transaction.atomic():
            # Mettre à jour le mot de passe et marquer l'inscription comme complétée
            pre_registered_user.set_password(password)
            pre_registered_user.registration_completed = True
            pre_registered_user.is_active = True
            pre_registered_user.save()

            # Créer les entrées FreeRADIUS pour l'accès au portail captif

            # 1. Créer/Mettre à jour l'authentification dans radcheck
            RadCheck.objects.update_or_create(
                username=pre_registered_user.username,
                attribute='Cleartext-Password',
                defaults={
                    'op': ':=',
                    'value': password
                }
            )

            # 2. Définir le timeout de session basé sur le rôle
            session_timeout = 86400 if pre_registered_user.role == 'admin' else 3600
            RadReply.objects.update_or_create(
                username=pre_registered_user.username,
                attribute='Session-Timeout',
                defaults={
                    'op': '=',
                    'value': str(session_timeout)
                }
            )

            # 3. Ajouter la limite de bande passante par défaut (10Mbps)
            RadReply.objects.update_or_create(
                username=pre_registered_user.username,
                attribute='Mikrotik-Rate-Limit',
                defaults={
                    'op': '=',
                    'value': '10M/10M'
                }
            )

            # 4. Assigner au groupe utilisateur
            RadUserGroup.objects.update_or_create(
                username=pre_registered_user.username,
                groupname=pre_registered_user.role,
                defaults={'priority': 0}
            )

            # Générer les tokens JWT
            refresh = RefreshToken.for_user(pre_registered_user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # Create response
            response = Response({
                'user': {
                    'id': pre_registered_user.id,
                    'username': pre_registered_user.username,
                    'email': pre_registered_user.email,
                    'first_name': pre_registered_user.first_name,
                    'last_name': pre_registered_user.last_name,
                    'promotion': pre_registered_user.promotion,
                    'matricule': pre_registered_user.matricule,
                    'role': pre_registered_user.role
                },
                'tokens': {
                    'refresh': refresh_token,
                    'access': access_token,
                },
                'message': 'Inscription réussie ! Vous pouvez maintenant vous connecter au portail captif.',
                'auth_method': 'cookie',  # Indicate that cookies are being used
                'radius_info': {
                    'username': pre_registered_user.username,
                    'session_timeout': f'{session_timeout//3600}h',
                    'bandwidth_limit': '10M/10M',
                    'can_access_captive_portal': True
                }
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
@permission_classes([IsAuthenticated, IsAdmin])
def admin_preregister_user(request):
    """
    Admin endpoint to pre-register users.
    Creates user accounts with default password that users must complete later.

    Required fields: first_name, last_name, promotion, matricule
    Optional fields: username, email
    """
    serializer = AdminUserCreationSerializer(data=request.data)

    if serializer.is_valid():
        try:
            # Créer l'utilisateur pré-enregistré
            user = serializer.save()

            # Récupérer le mot de passe temporaire généré
            temporary_password = getattr(user, '_temporary_password', None)

            return Response({
                'success': True,
                'message': 'Utilisateur pré-enregistré avec succès',
                'user': {
                    'id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'promotion': user.promotion,
                    'matricule': user.matricule,
                    'username': user.username,
                    'email': user.email,
                    'is_pre_registered': user.is_pre_registered,
                    'registration_completed': user.registration_completed,
                    'created_at': user.created_at
                },
                'credentials': {
                    'username': user.username,
                    'temporary_password': temporary_password,
                    'note': 'IMPORTANT: Ce mot de passe ne sera affiché qu\'une seule fois. '
                           'Communiquez-le à l\'utilisateur de manière sécurisée (email, SMS, etc.). '
                           'L\'utilisateur devra le changer lors de sa première connexion.'
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'error': 'Erreur lors de la pré-inscription',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

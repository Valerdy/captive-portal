from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from .serializers import UserSerializer
from .models import Session, Device, User
from .permissions import IsAdmin

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
def register(request):
    """
    User registration endpoint
    Creates user in both Django and FreeRADIUS for Mikrotik captive portal access
    """
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        # Get the plain password before it's hashed
        plain_password = request.data.get('password')

        # Use transaction to ensure both Django and RADIUS user are created together
        try:
            with transaction.atomic():
                # Create Django user (password will be hashed)
                user = serializer.save()

                # Create FreeRADIUS user with plain password for captive portal authentication
                # This allows the user to login to Mikrotik captive portal

                # 1. Create authentication entry in radcheck
                RadCheck.objects.create(
                    username=user.username,
                    attribute='Cleartext-Password',
                    op=':=',
                    value=plain_password
                )

                # 2. Set session timeout based on role (user = 1h, admin = 24h)
                session_timeout = 86400 if user.role == 'admin' else 3600
                RadReply.objects.update_or_create(
                    username=user.username,
                    attribute='Session-Timeout',
                    defaults={
                        'op': '=',
                        'value': str(session_timeout)
                    }
                )

                # 3. Add default bandwidth limit (10Mbps up/down) - optional
                RadReply.objects.update_or_create(
                    username=user.username,
                    attribute='Mikrotik-Rate-Limit',
                    defaults={
                        'op': '=',
                        'value': '10M/10M'
                    }
                )

                # 4. Assign to user group
                RadUserGroup.objects.update_or_create(
                    username=user.username,
                    groupname=user.role,
                    defaults={'priority': 0}
                )

                # Generate tokens for the new user
                refresh = RefreshToken.for_user(user)

                return Response({
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    },
                    'message': 'User registered successfully. You can now login to the Mikrotik captive portal.',
                    'radius_info': {
                        'username': user.username,
                        'session_timeout': f'{session_timeout//3600}h',
                        'bandwidth_limit': '10M/10M',
                        'can_access_captive_portal': True
                    }
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'error': 'Failed to create user',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
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

    return Response({
        'user': UserSerializer(user).data,
        'tokens': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        },
        'message': 'Login successful'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    User logout endpoint - blacklist the refresh token
    """
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()

        return Response(
            {'message': 'Logout successful'},
            status=status.HTTP_200_OK
        )
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

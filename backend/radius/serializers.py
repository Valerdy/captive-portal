from rest_framework import serializers
from .models import (
    RadiusServer, RadiusAuthLog, RadiusAccounting, RadiusClient,
    RadCheck, RadReply, RadUserGroup, RadGroupCheck, RadGroupReply, RadPostAuth
)


class RadiusServerSerializer(serializers.ModelSerializer):
    """Serializer for RadiusServer model"""

    class Meta:
        model = RadiusServer
        fields = [
            'id', 'name', 'host', 'auth_port', 'acct_port', 'secret',
            'is_active', 'timeout', 'retries', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'secret': {'write_only': True}
        }


class RadiusServerListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing RADIUS servers"""

    class Meta:
        model = RadiusServer
        fields = ['id', 'name', 'host', 'auth_port', 'acct_port', 'is_active']
        read_only_fields = fields


class RadiusAuthLogSerializer(serializers.ModelSerializer):
    """Serializer for RadiusAuthLog model"""
    server_name = serializers.CharField(source='server.name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = RadiusAuthLog
        fields = [
            'id', 'server', 'server_name', 'user', 'user_username',
            'username', 'mac_address', 'ip_address', 'nas_ip_address',
            'nas_port', 'status', 'reply_message', 'timestamp',
            'request_data', 'response_data'
        ]
        read_only_fields = ['id', 'timestamp']


class RadiusAccountingSerializer(serializers.ModelSerializer):
    """Serializer for RadiusAccounting model"""
    server_name = serializers.CharField(source='server.name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    total_octets = serializers.IntegerField(read_only=True)

    class Meta:
        model = RadiusAccounting
        fields = [
            'id', 'server', 'server_name', 'user', 'user_username',
            'session_id', 'username', 'mac_address',
            'framed_ip_address', 'nas_ip_address', 'nas_port',
            'status_type', 'termination_cause', 'session_time',
            'start_time', 'stop_time', 'input_octets', 'output_octets',
            'input_packets', 'output_packets', 'input_gigawords',
            'output_gigawords', 'total_octets', 'timestamp', 'raw_data'
        ]
        read_only_fields = ['id', 'timestamp', 'total_octets']


class RadiusAccountingListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing accounting records"""
    total_octets = serializers.IntegerField(read_only=True)

    class Meta:
        model = RadiusAccounting
        fields = [
            'id', 'session_id', 'username', 'status_type',
            'session_time', 'total_octets', 'timestamp'
        ]
        read_only_fields = fields


class RadiusClientSerializer(serializers.ModelSerializer):
    """Serializer for RadiusClient model"""

    class Meta:
        model = RadiusClient
        fields = [
            'id', 'name', 'shortname', 'nas_type', 'ip_address',
            'secret', 'description', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'secret': {'write_only': True}
        }


# ============================================================================
# FreeRADIUS User Management Serializers
# ============================================================================

class RadCheckSerializer(serializers.ModelSerializer):
    """Serializer for RadCheck model (user authentication)"""

    class Meta:
        model = RadCheck
        fields = ['id', 'username', 'attribute', 'op', 'value']
        read_only_fields = ['id']
        extra_kwargs = {
            'value': {'write_only': True}  # Hide password in responses
        }


class RadReplySerializer(serializers.ModelSerializer):
    """Serializer for RadReply model (user reply attributes)"""

    class Meta:
        model = RadReply
        fields = ['id', 'username', 'attribute', 'op', 'value']
        read_only_fields = ['id']


class RadUserGroupSerializer(serializers.ModelSerializer):
    """Serializer for RadUserGroup model (user-group mapping)"""

    class Meta:
        model = RadUserGroup
        fields = ['id', 'username', 'groupname', 'priority']
        read_only_fields = ['id']


class RadGroupCheckSerializer(serializers.ModelSerializer):
    """Serializer for RadGroupCheck model (group checks)"""

    class Meta:
        model = RadGroupCheck
        fields = ['id', 'groupname', 'attribute', 'op', 'value']
        read_only_fields = ['id']


class RadGroupReplySerializer(serializers.ModelSerializer):
    """Serializer for RadGroupReply model (group replies)"""

    class Meta:
        model = RadGroupReply
        fields = ['id', 'groupname', 'attribute', 'op', 'value', 'priority']
        read_only_fields = ['id']


class RadPostAuthSerializer(serializers.ModelSerializer):
    """Serializer for RadPostAuth model (authentication logs)"""

    class Meta:
        model = RadPostAuth
        fields = ['id', 'username', 'pass_field', 'reply', 'authdate']
        read_only_fields = fields  # Read-only, logs are created by FreeRADIUS


class RadiusUserSerializer(serializers.Serializer):
    """
    Combined serializer for creating/updating a complete RADIUS user
    Handles creation in radcheck, radreply, and radusergroup tables
    """
    username = serializers.CharField(max_length=64, required=True)
    password = serializers.CharField(max_length=253, required=True, write_only=True)
    groupname = serializers.ChoiceField(
        choices=['admin', 'user'],
        default='user',
        help_text='User group (admin or user)'
    )
    session_timeout = serializers.IntegerField(
        default=3600,
        help_text='Session timeout in seconds (default: 3600 = 1 hour)'
    )
    bandwidth_limit = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        help_text='Bandwidth limit (e.g., "10M/10M" for Mikrotik)'
    )

    def create(self, validated_data):
        """Create a complete RADIUS user with all necessary entries"""
        username = validated_data['username']
        password = validated_data['password']
        groupname = validated_data.get('groupname', 'user')
        session_timeout = validated_data.get('session_timeout', 3600)
        bandwidth_limit = validated_data.get('bandwidth_limit')

        # Create authentication entry in radcheck
        rad_check, _ = RadCheck.objects.update_or_create(
            username=username,
            attribute='Cleartext-Password',
            defaults={
                'value': password,
                'op': ':='
            }
        )

        # Create session timeout in radreply
        RadReply.objects.update_or_create(
            username=username,
            attribute='Session-Timeout',
            defaults={
                'value': str(session_timeout),
                'op': '='
            }
        )

        # Add bandwidth limit if provided
        if bandwidth_limit:
            RadReply.objects.update_or_create(
                username=username,
                attribute='Mikrotik-Rate-Limit',
                defaults={
                    'value': bandwidth_limit,
                    'op': '='
                }
            )

        # Assign to group in radusergroup
        RadUserGroup.objects.update_or_create(
            username=username,
            groupname=groupname,
            defaults={
                'priority': 0
            }
        )

        return validated_data

    def update(self, instance, validated_data):
        """Update RADIUS user entries"""
        username = validated_data.get('username', instance.get('username'))
        password = validated_data.get('password')
        groupname = validated_data.get('groupname')
        session_timeout = validated_data.get('session_timeout')
        bandwidth_limit = validated_data.get('bandwidth_limit')

        # Update password if provided
        if password:
            RadCheck.objects.update_or_create(
                username=username,
                attribute='Cleartext-Password',
                defaults={
                    'value': password,
                    'op': ':='
                }
            )

        # Update session timeout if provided
        if session_timeout:
            RadReply.objects.update_or_create(
                username=username,
                attribute='Session-Timeout',
                defaults={
                    'value': str(session_timeout),
                    'op': '='
                }
            )

        # Update bandwidth limit if provided
        if bandwidth_limit:
            RadReply.objects.update_or_create(
                username=username,
                attribute='Mikrotik-Rate-Limit',
                defaults={
                    'value': bandwidth_limit,
                    'op': '='
                }
            )

        # Update group if provided
        if groupname:
            # Remove old group assignments
            RadUserGroup.objects.filter(username=username).delete()
            # Add new group
            RadUserGroup.objects.create(
                username=username,
                groupname=groupname,
                priority=0
            )

        return validated_data

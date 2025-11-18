from rest_framework import serializers
from .models import RadiusServer, RadiusAuthLog, RadiusAccounting, RadiusClient


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

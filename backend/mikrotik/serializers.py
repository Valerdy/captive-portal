from rest_framework import serializers
from .models import MikrotikRouter, MikrotikHotspotUser, MikrotikActiveConnection, MikrotikLog


class MikrotikRouterSerializer(serializers.ModelSerializer):
    """Serializer for MikrotikRouter model"""

    class Meta:
        model = MikrotikRouter
        fields = [
            'id', 'name', 'host', 'port', 'username', 'password',
            'use_ssl', 'is_active', 'description',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }


class MikrotikRouterListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing routers"""

    class Meta:
        model = MikrotikRouter
        fields = ['id', 'name', 'host', 'port', 'is_active', 'description']
        read_only_fields = fields


class MikrotikHotspotUserSerializer(serializers.ModelSerializer):
    """Serializer for MikrotikHotspotUser model"""
    router_name = serializers.CharField(source='router.name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = MikrotikHotspotUser
        fields = [
            'id', 'router', 'router_name', 'user', 'user_username',
            'username', 'password', 'mac_address', 'ip_address',
            'uptime_limit', 'bytes_in_limit', 'bytes_out_limit', 'rate_limit',
            'is_active', 'is_disabled', 'created_at', 'updated_at', 'last_sync'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_sync']
        extra_kwargs = {
            'password': {'write_only': True}
        }


class MikrotikActiveConnectionSerializer(serializers.ModelSerializer):
    """Serializer for MikrotikActiveConnection model"""
    router_name = serializers.CharField(source='router.name', read_only=True)
    hotspot_username = serializers.CharField(source='hotspot_user.username', read_only=True)

    class Meta:
        model = MikrotikActiveConnection
        fields = [
            'id', 'router', 'router_name', 'hotspot_user', 'hotspot_username',
            'session_id', 'username', 'mac_address', 'ip_address',
            'uptime', 'bytes_in', 'bytes_out', 'packets_in', 'packets_out',
            'login_time', 'last_update'
        ]
        read_only_fields = ['id', 'last_update']


class MikrotikLogSerializer(serializers.ModelSerializer):
    """Serializer for MikrotikLog model"""
    router_name = serializers.CharField(source='router.name', read_only=True)

    class Meta:
        model = MikrotikLog
        fields = [
            'id', 'router', 'router_name', 'level', 'operation',
            'message', 'details', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class MikrotikSyncSerializer(serializers.Serializer):
    """Serializer for Mikrotik synchronization operations"""
    router_id = serializers.IntegerField(required=True)
    operation = serializers.ChoiceField(
        choices=['sync_users', 'sync_active', 'full_sync'],
        required=True
    )

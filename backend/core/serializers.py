from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Device, Session, Voucher


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'password2',
            'first_name', 'last_name', 'phone_number', 'mac_address',
            'ip_address', 'is_voucher_user', 'voucher_code',
            'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'date_joined', 'created_at', 'updated_at', 'is_active', 'is_staff', 'is_superuser']

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password2'):
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class UserListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing users"""
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'mac_address', 'ip_address',
            'is_voucher_user', 'is_active', 'is_staff', 'is_superuser',
            'date_joined'
        ]
        read_only_fields = fields


class DeviceSerializer(serializers.ModelSerializer):
    """Serializer for Device model"""
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Device
        fields = [
            'id', 'user', 'user_username', 'mac_address', 'ip_address',
            'hostname', 'user_agent', 'device_type',
            'first_seen', 'last_seen', 'is_active'
        ]
        read_only_fields = ['id', 'first_seen', 'last_seen']


class SessionSerializer(serializers.ModelSerializer):
    """Serializer for Session model"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    device_mac = serializers.CharField(source='device.mac_address', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    total_bytes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Session
        fields = [
            'id', 'user', 'user_username', 'device', 'device_mac',
            'session_id', 'ip_address', 'mac_address', 'status',
            'start_time', 'end_time', 'timeout_duration',
            'bytes_in', 'bytes_out', 'packets_in', 'packets_out',
            'is_expired', 'total_bytes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_expired', 'total_bytes']


class SessionListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing sessions"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    total_bytes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Session
        fields = [
            'id', 'user_username', 'session_id', 'ip_address',
            'mac_address', 'status', 'start_time', 'total_bytes'
        ]
        read_only_fields = fields


class VoucherSerializer(serializers.ModelSerializer):
    """Serializer for Voucher model"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    used_by_username = serializers.CharField(source='used_by.username', read_only=True)
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = Voucher
        fields = [
            'id', 'code', 'status', 'duration', 'max_devices', 'used_count',
            'valid_from', 'valid_until', 'used_by', 'used_by_username',
            'used_at', 'created_by', 'created_by_username', 'created_at',
            'notes', 'is_valid'
        ]
        read_only_fields = ['id', 'created_at', 'used_count', 'is_valid']


class VoucherValidationSerializer(serializers.Serializer):
    """Serializer for voucher validation"""
    code = serializers.CharField(max_length=50, required=True)

    def validate_code(self, value):
        try:
            voucher = Voucher.objects.get(code=value)
            if not voucher.is_valid:
                raise serializers.ValidationError("This voucher is not valid or has expired.")
            return value
        except Voucher.DoesNotExist:
            raise serializers.ValidationError("Invalid voucher code.")

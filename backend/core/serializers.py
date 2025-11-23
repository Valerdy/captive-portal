from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Device, Session, Voucher, Role


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model"""
    class Meta:
        model = Role
        fields = ['id', 'name', 'description']
        read_only_fields = ['id']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    role_name = serializers.SerializerMethodField()
    role_detail = RoleSerializer(source='role', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'password2',
            'first_name', 'last_name', 'phone_number', 'mac_address',
            'ip_address', 'is_voucher_user', 'voucher_code',
            'is_active', 'is_staff', 'is_superuser',
            'role', 'role_name', 'role_detail',
            'date_joined', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'date_joined', 'created_at', 'updated_at', 'role', 'role_name', 'role_detail']

    def get_role_name(self, obj):
        """Get the role name (synced with is_staff/is_superuser)"""
        return obj.get_role_name()

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password2'):
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        is_staff = validated_data.pop('is_staff', False)
        is_superuser = validated_data.pop('is_superuser', False)

        user = User.objects.create_user(password=password, **validated_data)
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.save()
        return user

    def update(self, instance, validated_data):
        # Remove password fields if present (password updates should use separate endpoint)
        validated_data.pop('password', None)
        validated_data.pop('password2', None)

        # Update is_staff and is_superuser if provided
        if 'is_staff' in validated_data:
            instance.is_staff = validated_data.pop('is_staff')
        if 'is_superuser' in validated_data:
            instance.is_superuser = validated_data.pop('is_superuser')
        if 'is_active' in validated_data:
            instance.is_active = validated_data.pop('is_active')

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class UserListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing users"""
    role_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'mac_address', 'ip_address',
            'is_voucher_user', 'is_active', 'is_staff', 'is_superuser',
            'role_name', 'date_joined'
        ]
        read_only_fields = fields

    def get_role_name(self, obj):
        """Get the role name"""
        return obj.get_role_name()


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

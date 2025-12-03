from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Device, Session, Voucher, BlockedSite, UserQuota
from .utils import generate_secure_password


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    role_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'password2',
            'first_name', 'last_name', 'promotion', 'matricule',
            'phone_number', 'mac_address',
            'ip_address', 'is_voucher_user', 'voucher_code',
            'is_active', 'is_staff', 'is_superuser',
            'is_radius_activated',
            'role', 'role_name',
            'date_joined', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'date_joined', 'created_at', 'updated_at', 'role_name', 'is_radius_activated']

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
        # Stocker le mot de passe en clair pour l'activation RADIUS
        user.cleartext_password = password
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
            'promotion', 'matricule', 'phone_number', 'mac_address', 'ip_address',
            'is_voucher_user', 'is_active', 'is_staff', 'is_superuser',
            'is_radius_activated',
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


class BlockedSiteSerializer(serializers.ModelSerializer):
    """Serializer for BlockedSite model"""
    added_by_username = serializers.CharField(source='added_by.username', read_only=True)

    class Meta:
        model = BlockedSite
        fields = [
            'id', 'url', 'type', 'reason', 'is_active',
            'added_by', 'added_by_username', 'added_date', 'updated_at'
        ]
        read_only_fields = ['id', 'added_by', 'added_by_username', 'added_date', 'updated_at']

    def create(self, validated_data):
        # Add the current user as the creator
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['added_by'] = request.user
        return super().create(validated_data)


class UserQuotaSerializer(serializers.ModelSerializer):
    """Serializer for UserQuota model"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    daily_usage_percent = serializers.FloatField(read_only=True)
    weekly_usage_percent = serializers.FloatField(read_only=True)
    monthly_usage_percent = serializers.FloatField(read_only=True)

    # Convert bytes to GB for easier reading
    daily_limit_gb = serializers.SerializerMethodField()
    weekly_limit_gb = serializers.SerializerMethodField()
    monthly_limit_gb = serializers.SerializerMethodField()
    used_today_gb = serializers.SerializerMethodField()
    used_week_gb = serializers.SerializerMethodField()
    used_month_gb = serializers.SerializerMethodField()

    class Meta:
        model = UserQuota
        fields = [
            'id', 'user', 'user_username',
            'daily_limit', 'weekly_limit', 'monthly_limit',
            'daily_limit_gb', 'weekly_limit_gb', 'monthly_limit_gb',
            'used_today', 'used_week', 'used_month',
            'used_today_gb', 'used_week_gb', 'used_month_gb',
            'daily_usage_percent', 'weekly_usage_percent', 'monthly_usage_percent',
            'last_daily_reset', 'last_weekly_reset', 'last_monthly_reset',
            'is_active', 'is_exceeded',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_username', 'used_today', 'used_week', 'used_month',
            'last_daily_reset', 'last_weekly_reset', 'last_monthly_reset',
            'is_exceeded', 'created_at', 'updated_at',
            'daily_usage_percent', 'weekly_usage_percent', 'monthly_usage_percent',
            'daily_limit_gb', 'weekly_limit_gb', 'monthly_limit_gb',
            'used_today_gb', 'used_week_gb', 'used_month_gb'
        ]

    def get_daily_limit_gb(self, obj):
        return round(obj.daily_limit / (1024 ** 3), 2)

    def get_weekly_limit_gb(self, obj):
        return round(obj.weekly_limit / (1024 ** 3), 2)

    def get_monthly_limit_gb(self, obj):
        return round(obj.monthly_limit / (1024 ** 3), 2)

    def get_used_today_gb(self, obj):
        return round(obj.used_today / (1024 ** 3), 2)

    def get_used_week_gb(self, obj):
        return round(obj.used_week / (1024 ** 3), 2)

    def get_used_month_gb(self, obj):
        return round(obj.used_month / (1024 ** 3), 2)

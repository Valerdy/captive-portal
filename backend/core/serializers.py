from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import (
    User, Device, Session, Voucher, BlockedSite, UserQuota, Promotion, Profile,
    UserProfileUsage, ProfileHistory, ProfileAlert, UserDisconnectionLog
)
from .utils import generate_secure_password


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for Profile model"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    data_volume_gb = serializers.FloatField(read_only=True)
    bandwidth_upload_mbps = serializers.FloatField(read_only=True)
    bandwidth_download_mbps = serializers.FloatField(read_only=True)
    daily_limit_gb = serializers.FloatField(read_only=True)
    weekly_limit_gb = serializers.FloatField(read_only=True)
    monthly_limit_gb = serializers.FloatField(read_only=True)

    # Nombre d'utilisateurs et promotions utilisant ce profil
    users_count = serializers.SerializerMethodField()
    promotions_count = serializers.SerializerMethodField()

    # Champs pour assigner ce profil à des promotions/utilisateurs
    assign_to_promotions = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="Liste des IDs de promotions à assigner à ce profil"
    )
    assign_to_users = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="Liste des IDs d'utilisateurs à assigner à ce profil"
    )

    class Meta:
        model = Profile
        fields = [
            'id', 'name', 'description', 'is_active',
            'bandwidth_upload', 'bandwidth_download',
            'bandwidth_upload_mbps', 'bandwidth_download_mbps',
            'quota_type', 'data_volume', 'data_volume_gb',
            'daily_limit', 'weekly_limit', 'monthly_limit',
            'daily_limit_gb', 'weekly_limit_gb', 'monthly_limit_gb',
            'validity_duration', 'session_timeout', 'idle_timeout',
            'simultaneous_use', 'created_by', 'created_by_username',
            'created_at', 'updated_at',
            'users_count', 'promotions_count',
            'assign_to_promotions', 'assign_to_users'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'created_by_username',
            'data_volume_gb', 'bandwidth_upload_mbps', 'bandwidth_download_mbps',
            'daily_limit_gb', 'weekly_limit_gb', 'monthly_limit_gb',
            'users_count', 'promotions_count'
        ]

    def get_users_count(self, obj):
        """Nombre d'utilisateurs utilisant ce profil (directement)"""
        return obj.users.count()

    def get_promotions_count(self, obj):
        """Nombre de promotions utilisant ce profil"""
        return obj.promotions.count()

    def create(self, validated_data):
        # Extraire les listes d'assignation
        promotion_ids = validated_data.pop('assign_to_promotions', [])
        user_ids = validated_data.pop('assign_to_users', [])

        # Ajouter l'utilisateur courant comme créateur
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user

        # Créer le profil
        profile = super().create(validated_data)

        # Assigner le profil aux promotions sélectionnées
        if promotion_ids:
            Promotion.objects.filter(id__in=promotion_ids).update(profile=profile)

        # Assigner le profil aux utilisateurs sélectionnés
        if user_ids:
            User.objects.filter(id__in=user_ids).update(profile=profile)

        return profile

    def update(self, instance, validated_data):
        # Extraire les listes d'assignation
        promotion_ids = validated_data.pop('assign_to_promotions', None)
        user_ids = validated_data.pop('assign_to_users', None)

        # Mettre à jour le profil
        profile = super().update(instance, validated_data)

        # Assigner le profil aux promotions sélectionnées (si fourni)
        if promotion_ids is not None:
            # Retirer ce profil de toutes les promotions actuelles
            Promotion.objects.filter(profile=profile).update(profile=None)
            # Assigner aux nouvelles promotions
            if promotion_ids:
                Promotion.objects.filter(id__in=promotion_ids).update(profile=profile)

        # Assigner le profil aux utilisateurs sélectionnés (si fourni)
        if user_ids is not None:
            # Retirer ce profil de tous les utilisateurs actuels
            User.objects.filter(profile=profile).update(profile=None)
            # Assigner aux nouveaux utilisateurs
            if user_ids:
                User.objects.filter(id__in=user_ids).update(profile=profile)

        return profile


class PromotionSerializer(serializers.ModelSerializer):
    profile_name = serializers.CharField(source='profile.name', read_only=True)
    user_count = serializers.SerializerMethodField()
    active_user_count = serializers.SerializerMethodField()

    class Meta:
        model = Promotion
        fields = ['id', 'name', 'profile', 'profile_name', 'is_active', 'created_at', 'updated_at', 'user_count', 'active_user_count']
        read_only_fields = ['created_at', 'updated_at', 'profile_name', 'user_count', 'active_user_count']

    def get_user_count(self, obj):
        """Nombre total d'utilisateurs dans la promotion"""
        return obj.users.count()

    def get_active_user_count(self, obj):
        """Nombre d'utilisateurs actifs dans la promotion"""
        return obj.users.filter(is_active=True).count()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    role_name = serializers.SerializerMethodField()
    promotion_name = serializers.CharField(source='promotion.name', read_only=True)
    profile_name = serializers.CharField(source='profile.name', read_only=True)
    effective_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'password2',
            'first_name', 'last_name', 'promotion', 'promotion_name', 'matricule',
            'profile', 'profile_name', 'effective_profile',
            'phone_number', 'mac_address',
            'ip_address', 'is_voucher_user', 'voucher_code',
            'is_active', 'is_staff', 'is_superuser',
            'is_radius_activated', 'is_radius_enabled',
            'role', 'role_name',
            'date_joined', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'date_joined', 'created_at', 'updated_at', 'role_name', 'is_radius_activated', 'promotion_name', 'profile_name', 'effective_profile']

    def get_effective_profile(self, obj):
        """Retourne les informations du profil effectif de l'utilisateur"""
        profile = obj.get_effective_profile()
        if profile:
            return {
                'id': profile.id,
                'name': profile.name,
                'quota_type': profile.quota_type,
                'data_volume_gb': profile.data_volume_gb,
                'bandwidth_upload_mbps': profile.bandwidth_upload_mbps,
                'bandwidth_download_mbps': profile.bandwidth_download_mbps,
                'validity_duration': profile.validity_duration
            }
        return None

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
    promotion_name = serializers.CharField(source='promotion.name', read_only=True)
    profile_name = serializers.CharField(source='profile.name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'promotion', 'promotion_name', 'profile', 'profile_name', 'matricule',
            'phone_number', 'mac_address', 'ip_address',
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


class UserProfileUsageSerializer(serializers.ModelSerializer):
    """Serializer for UserProfileUsage model"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    effective_profile = serializers.SerializerMethodField()

    # Pourcentages d'utilisation
    daily_usage_percent = serializers.FloatField(read_only=True)
    weekly_usage_percent = serializers.FloatField(read_only=True)
    monthly_usage_percent = serializers.FloatField(read_only=True)
    total_usage_percent = serializers.FloatField(read_only=True)

    # Conversions en Go
    used_today_gb = serializers.FloatField(read_only=True)
    used_week_gb = serializers.FloatField(read_only=True)
    used_month_gb = serializers.FloatField(read_only=True)
    used_total_gb = serializers.FloatField(read_only=True)

    # Informations d'expiration
    is_expired = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()

    class Meta:
        model = UserProfileUsage
        fields = [
            'id', 'user', 'user_username', 'effective_profile',
            'used_today', 'used_week', 'used_month', 'used_total',
            'used_today_gb', 'used_week_gb', 'used_month_gb', 'used_total_gb',
            'daily_usage_percent', 'weekly_usage_percent',
            'monthly_usage_percent', 'total_usage_percent',
            'last_daily_reset', 'last_weekly_reset', 'last_monthly_reset',
            'activation_date', 'is_exceeded', 'is_active',
            'is_expired', 'days_remaining',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_username', 'effective_profile',
            'used_today', 'used_week', 'used_month', 'used_total',
            'used_today_gb', 'used_week_gb', 'used_month_gb', 'used_total_gb',
            'daily_usage_percent', 'weekly_usage_percent',
            'monthly_usage_percent', 'total_usage_percent',
            'last_daily_reset', 'last_weekly_reset', 'last_monthly_reset',
            'is_exceeded', 'is_expired', 'days_remaining',
            'created_at', 'updated_at'
        ]

    def get_effective_profile(self, obj):
        """Retourne le profil effectif de l'utilisateur"""
        profile = obj.get_effective_profile()
        if profile:
            return {
                'id': profile.id,
                'name': profile.name,
                'quota_type': profile.quota_type,
                'data_volume_gb': profile.data_volume_gb,
                'daily_limit_gb': profile.daily_limit_gb,
                'weekly_limit_gb': profile.weekly_limit_gb,
                'monthly_limit_gb': profile.monthly_limit_gb,
            }
        return None

    def get_is_expired(self, obj):
        """Vérifie si le profil est expiré"""
        return obj.is_expired()

    def get_days_remaining(self, obj):
        """Retourne le nombre de jours restants"""
        return obj.days_remaining()


class ProfileHistorySerializer(serializers.ModelSerializer):
    """Serializer for ProfileHistory model"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    old_profile_name = serializers.CharField(source='old_profile.name', read_only=True)
    new_profile_name = serializers.CharField(source='new_profile.name', read_only=True)
    changed_by_username = serializers.CharField(source='changed_by.username', read_only=True)

    class Meta:
        model = ProfileHistory
        fields = [
            'id', 'user', 'user_username',
            'old_profile', 'old_profile_name',
            'new_profile', 'new_profile_name',
            'changed_by', 'changed_by_username',
            'changed_at', 'reason', 'change_type'
        ]
        read_only_fields = [
            'id', 'user_username', 'old_profile_name',
            'new_profile_name', 'changed_by_username', 'changed_at'
        ]

    def create(self, validated_data):
        # Ajouter l'utilisateur courant comme auteur du changement
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['changed_by'] = request.user
        return super().create(validated_data)


class ProfileAlertSerializer(serializers.ModelSerializer):
    """Serializer for ProfileAlert model"""
    profile_name = serializers.CharField(source='profile.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = ProfileAlert
        fields = [
            'id', 'profile', 'profile_name',
            'alert_type', 'threshold_percent', 'threshold_days',
            'notification_method', 'is_active', 'message_template',
            'created_by', 'created_by_username',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'profile_name', 'created_by', 'created_by_username',
            'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        # Ajouter l'utilisateur courant comme créateur
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class UserDisconnectionLogSerializer(serializers.ModelSerializer):
    """Serializer for UserDisconnectionLog model"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.SerializerMethodField()
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)
    reconnected_by_username = serializers.CharField(source='reconnected_by.username', read_only=True)
    quota_used_gb = serializers.SerializerMethodField()
    quota_limit_gb = serializers.SerializerMethodField()
    duration_formatted = serializers.SerializerMethodField()

    class Meta:
        model = UserDisconnectionLog
        fields = [
            'id', 'user', 'user_username', 'user_full_name',
            'reason', 'reason_display', 'description',
            'disconnected_at', 'reconnected_at', 'is_active',
            'reconnected_by', 'reconnected_by_username',
            'quota_used', 'quota_limit', 'quota_used_gb', 'quota_limit_gb',
            'session_duration', 'duration_formatted'
        ]
        read_only_fields = [
            'id', 'disconnected_at', 'reconnected_at', 'is_active',
            'user_username', 'user_full_name', 'reason_display',
            'reconnected_by_username', 'quota_used_gb', 'quota_limit_gb',
            'duration_formatted'
        ]

    def get_user_full_name(self, obj):
        """Retourne le nom complet de l'utilisateur"""
        return f"{obj.user.first_name} {obj.user.last_name}"

    def get_quota_used_gb(self, obj):
        """Retourne le quota utilisé en Go"""
        if obj.quota_used:
            return round(obj.quota_used / (1024**3), 2)
        return None

    def get_quota_limit_gb(self, obj):
        """Retourne la limite de quota en Go"""
        if obj.quota_limit:
            return round(obj.quota_limit / (1024**3), 2)
        return None

    def get_duration_formatted(self, obj):
        """Retourne la durée de session formatée"""
        if obj.session_duration:
            hours = obj.session_duration // 3600
            minutes = (obj.session_duration % 3600) // 60
            return f"{hours}h{minutes:02d}m"
        return None

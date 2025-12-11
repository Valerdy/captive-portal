from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Device, Session, Voucher, Promotion, Profile,
    UserProfileUsage, ProfileHistory, ProfileAlert
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model"""
    list_display = [
        'username', 'email', 'first_name', 'last_name',
        'promotion', 'profile', 'phone_number', 'mac_address',
        'is_voucher_user', 'is_active'
    ]
    list_filter = ['is_active', 'is_staff', 'is_voucher_user', 'date_joined', 'promotion', 'profile']
    search_fields = ['username', 'email', 'phone_number', 'mac_address', 'promotion__name', 'profile__name']
    ordering = ['-date_joined']
    autocomplete_fields = ['promotion', 'profile']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Captive Portal Info', {
            'fields': ('promotion', 'profile', 'matricule', 'phone_number', 'mac_address', 'ip_address', 'is_voucher_user', 'voucher_code')
        }),
        ('RADIUS Status', {
            'fields': ('is_radius_activated', 'is_radius_enabled', 'cleartext_password'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Captive Portal Info', {
            'fields': ('promotion', 'profile', 'matricule', 'phone_number', 'mac_address', 'ip_address', 'is_voucher_user', 'voucher_code')
        }),
    )


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ['name', 'profile', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'profile']
    search_fields = ['name']
    ordering = ['name']
    autocomplete_fields = ['profile']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Admin interface for Profile model"""
    list_display = [
        'name', 'quota_type', 'data_volume_display',
        'bandwidth_display', 'validity_duration', 'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'quota_type', 'validity_duration', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = [
        'created_at', 'updated_at',
        'data_volume_gb', 'bandwidth_upload_mbps', 'bandwidth_download_mbps',
        'daily_limit_gb', 'weekly_limit_gb', 'monthly_limit_gb'
    ]

    fieldsets = (
        ('Informations de base', {
            'fields': ('name', 'description', 'is_active', 'created_by')
        }),
        ('Bande passante', {
            'fields': ('bandwidth_upload', 'bandwidth_upload_mbps', 'bandwidth_download', 'bandwidth_download_mbps'),
            'description': 'Bande passante en Kbps (1 Mbps = 1024 Kbps)'
        }),
        ('Quota de données', {
            'fields': ('quota_type', 'data_volume', 'data_volume_gb', 'validity_duration'),
            'description': 'Volume en octets (1 Go = 1073741824 octets)'
        }),
        ('Limites périodiques (optionnel)', {
            'fields': (
                'daily_limit', 'daily_limit_gb',
                'weekly_limit', 'weekly_limit_gb',
                'monthly_limit', 'monthly_limit_gb'
            ),
            'description': 'Limites de consommation journalière, hebdomadaire et mensuelle',
            'classes': ('collapse',)
        }),
        ('Paramètres de session RADIUS', {
            'fields': ('session_timeout', 'idle_timeout', 'simultaneous_use'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def data_volume_display(self, obj):
        """Affiche le volume de données en Go"""
        return f"{obj.data_volume_gb} Go"
    data_volume_display.short_description = 'Volume de données'

    def bandwidth_display(self, obj):
        """Affiche la bande passante en Mbps"""
        return f"↑{obj.bandwidth_upload_mbps} / ↓{obj.bandwidth_download_mbps} Mbps"
    bandwidth_display.short_description = 'Bande passante (UP/DOWN)'


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """Admin interface for Device model"""
    list_display = [
        'mac_address', 'user', 'ip_address', 'device_type',
        'is_active', 'first_seen', 'last_seen'
    ]
    list_filter = ['is_active', 'device_type', 'first_seen']
    search_fields = ['mac_address', 'ip_address', 'hostname', 'user__username']
    readonly_fields = ['first_seen', 'last_seen']
    ordering = ['-last_seen']


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    """Admin interface for Session model"""
    list_display = [
        'session_id', 'user', 'ip_address', 'mac_address',
        'status', 'start_time', 'total_bytes'
    ]
    list_filter = ['status', 'start_time']
    search_fields = ['session_id', 'user__username', 'ip_address', 'mac_address']
    readonly_fields = ['created_at', 'updated_at', 'start_time', 'is_expired', 'total_bytes']
    ordering = ['-start_time']

    fieldsets = (
        ('Session Info', {
            'fields': ('user', 'device', 'session_id', 'ip_address', 'mac_address', 'status')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time', 'timeout_duration', 'is_expired')
        }),
        ('Data Usage', {
            'fields': ('bytes_in', 'bytes_out', 'packets_in', 'packets_out', 'total_bytes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    """Admin interface for Voucher model"""
    list_display = [
        'code', 'status', 'duration', 'max_devices', 'used_count',
        'valid_from', 'valid_until', 'created_by', 'is_valid'
    ]
    list_filter = ['status', 'valid_from', 'valid_until', 'created_at']
    search_fields = ['code', 'created_by__username', 'used_by__username']
    readonly_fields = ['created_at', 'used_at', 'is_valid']
    ordering = ['-created_at']

    fieldsets = (
        ('Voucher Info', {
            'fields': ('code', 'status', 'duration', 'max_devices', 'used_count')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until', 'is_valid')
        }),
        ('Usage', {
            'fields': ('used_by', 'used_at')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'notes')
        }),
    )


@admin.register(UserProfileUsage)
class UserProfileUsageAdmin(admin.ModelAdmin):
    """Admin interface for UserProfileUsage model"""
    list_display = [
        'user', 'effective_profile_display', 'total_usage_gb_display',
        'daily_usage_display', 'is_exceeded', 'is_expired_display', 'is_active'
    ]
    list_filter = ['is_active', 'is_exceeded', 'activation_date']
    search_fields = ['user__username', 'user__email']
    readonly_fields = [
        'used_today_gb', 'used_week_gb', 'used_month_gb', 'used_total_gb',
        'daily_usage_percent', 'weekly_usage_percent',
        'monthly_usage_percent', 'total_usage_percent',
        'last_daily_reset', 'last_weekly_reset', 'last_monthly_reset',
        'created_at', 'updated_at'
    ]
    autocomplete_fields = ['user']
    ordering = ['-created_at']

    fieldsets = (
        ('Utilisateur', {
            'fields': ('user', 'is_active', 'activation_date')
        }),
        ('Consommation (octets)', {
            'fields': ('used_today', 'used_week', 'used_month', 'used_total')
        }),
        ('Consommation (Go)', {
            'fields': (
                'used_today_gb', 'used_week_gb',
                'used_month_gb', 'used_total_gb'
            ),
            'classes': ('collapse',)
        }),
        ('Pourcentages d\'utilisation', {
            'fields': (
                'daily_usage_percent', 'weekly_usage_percent',
                'monthly_usage_percent', 'total_usage_percent'
            ),
            'classes': ('collapse',)
        }),
        ('Dates de reset', {
            'fields': (
                'last_daily_reset', 'last_weekly_reset', 'last_monthly_reset'
            ),
            'classes': ('collapse',)
        }),
        ('Statut', {
            'fields': ('is_exceeded',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def effective_profile_display(self, obj):
        """Affiche le profil effectif"""
        profile = obj.get_effective_profile()
        return profile.name if profile else "Aucun"
    effective_profile_display.short_description = 'Profil effectif'

    def total_usage_gb_display(self, obj):
        """Affiche la consommation totale en Go"""
        return f"{obj.used_total_gb} Go"
    total_usage_gb_display.short_description = 'Total consommé'

    def daily_usage_display(self, obj):
        """Affiche la consommation journalière avec pourcentage"""
        return f"{obj.used_today_gb} Go ({round(obj.daily_usage_percent, 1)}%)"
    daily_usage_display.short_description = 'Aujourd\'hui'

    def is_expired_display(self, obj):
        """Affiche si le profil est expiré"""
        return obj.is_expired()
    is_expired_display.boolean = True
    is_expired_display.short_description = 'Expiré'


@admin.register(ProfileHistory)
class ProfileHistoryAdmin(admin.ModelAdmin):
    """Admin interface for ProfileHistory model"""
    list_display = [
        'user', 'change_type', 'old_profile', 'new_profile',
        'changed_by', 'changed_at'
    ]
    list_filter = ['change_type', 'changed_at']
    search_fields = [
        'user__username', 'old_profile__name',
        'new_profile__name', 'changed_by__username'
    ]
    readonly_fields = ['changed_at']
    autocomplete_fields = ['user', 'old_profile', 'new_profile', 'changed_by']
    ordering = ['-changed_at']

    fieldsets = (
        ('Changement', {
            'fields': ('user', 'change_type', 'old_profile', 'new_profile')
        }),
        ('Auteur et date', {
            'fields': ('changed_by', 'changed_at')
        }),
        ('Détails', {
            'fields': ('reason',)
        }),
    )


@admin.register(ProfileAlert)
class ProfileAlertAdmin(admin.ModelAdmin):
    """Admin interface for ProfileAlert model"""
    list_display = [
        'profile', 'alert_type', 'threshold_percent',
        'threshold_days', 'notification_method', 'is_active'
    ]
    list_filter = ['alert_type', 'notification_method', 'is_active', 'created_at']
    search_fields = ['profile__name', 'message_template']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['profile', 'created_by']
    ordering = ['-created_at']

    fieldsets = (
        ('Profil et type d\'alerte', {
            'fields': ('profile', 'alert_type', 'is_active')
        }),
        ('Seuils', {
            'fields': ('threshold_percent', 'threshold_days'),
            'description': 'threshold_percent pour alertes quota, threshold_days pour alertes expiration'
        }),
        ('Notification', {
            'fields': ('notification_method', 'message_template'),
            'description': 'Template peut contenir: {username}, {percent}, {remaining_gb}, {days_remaining}'
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

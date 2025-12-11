from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Device, Session, Voucher, Promotion, Profile


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
    readonly_fields = ['created_at', 'updated_at', 'data_volume_gb', 'bandwidth_upload_mbps', 'bandwidth_download_mbps']

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

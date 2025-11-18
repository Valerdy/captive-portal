from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Device, Session, Voucher


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model"""
    list_display = [
        'username', 'email', 'first_name', 'last_name',
        'phone_number', 'mac_address', 'is_voucher_user', 'is_active'
    ]
    list_filter = ['is_active', 'is_staff', 'is_voucher_user', 'date_joined']
    search_fields = ['username', 'email', 'phone_number', 'mac_address']
    ordering = ['-date_joined']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Captive Portal Info', {
            'fields': ('phone_number', 'mac_address', 'ip_address', 'is_voucher_user', 'voucher_code')
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Captive Portal Info', {
            'fields': ('phone_number', 'mac_address', 'ip_address', 'is_voucher_user', 'voucher_code')
        }),
    )


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

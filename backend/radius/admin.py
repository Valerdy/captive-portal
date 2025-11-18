from django.contrib import admin
from .models import RadiusServer, RadiusAuthLog, RadiusAccounting, RadiusClient


@admin.register(RadiusServer)
class RadiusServerAdmin(admin.ModelAdmin):
    """Admin interface for RadiusServer model"""
    list_display = ['name', 'host', 'auth_port', 'acct_port', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'host']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']

    fieldsets = (
        ('Server Info', {
            'fields': ('name', 'host', 'auth_port', 'acct_port', 'secret')
        }),
        ('Settings', {
            'fields': ('is_active', 'timeout', 'retries')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RadiusAuthLog)
class RadiusAuthLogAdmin(admin.ModelAdmin):
    """Admin interface for RadiusAuthLog model"""
    list_display = [
        'username', 'server', 'status', 'ip_address',
        'mac_address', 'nas_ip_address', 'timestamp'
    ]
    list_filter = ['status', 'server', 'timestamp']
    search_fields = ['username', 'ip_address', 'mac_address', 'nas_ip_address']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']

    fieldsets = (
        ('Authentication Info', {
            'fields': ('server', 'user', 'username', 'mac_address', 'ip_address')
        }),
        ('NAS Info', {
            'fields': ('nas_ip_address', 'nas_port')
        }),
        ('Result', {
            'fields': ('status', 'reply_message')
        }),
        ('Data', {
            'fields': ('request_data', 'response_data'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
    )


@admin.register(RadiusAccounting)
class RadiusAccountingAdmin(admin.ModelAdmin):
    """Admin interface for RadiusAccounting model"""
    list_display = [
        'session_id', 'username', 'status_type', 'framed_ip_address',
        'session_time', 'total_octets', 'timestamp'
    ]
    list_filter = ['status_type', 'termination_cause', 'server', 'timestamp']
    search_fields = ['session_id', 'username', 'framed_ip_address', 'mac_address']
    readonly_fields = ['timestamp', 'total_octets']
    ordering = ['-timestamp']

    fieldsets = (
        ('Session Info', {
            'fields': ('server', 'user', 'session_id', 'username', 'mac_address')
        }),
        ('Network Info', {
            'fields': ('framed_ip_address', 'nas_ip_address', 'nas_port')
        }),
        ('Status', {
            'fields': ('status_type', 'termination_cause')
        }),
        ('Timing', {
            'fields': ('session_time', 'start_time', 'stop_time')
        }),
        ('Data Usage', {
            'fields': (
                'input_octets', 'output_octets', 'input_packets', 'output_packets',
                'input_gigawords', 'output_gigawords', 'total_octets'
            )
        }),
        ('Raw Data', {
            'fields': ('raw_data',),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
    )


@admin.register(RadiusClient)
class RadiusClientAdmin(admin.ModelAdmin):
    """Admin interface for RadiusClient model"""
    list_display = ['name', 'shortname', 'ip_address', 'nas_type', 'is_active', 'created_at']
    list_filter = ['is_active', 'nas_type', 'created_at']
    search_fields = ['name', 'shortname', 'ip_address', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']

    fieldsets = (
        ('Client Info', {
            'fields': ('name', 'shortname', 'nas_type', 'ip_address', 'secret')
        }),
        ('Additional Info', {
            'fields': ('description', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

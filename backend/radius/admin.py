from django.contrib import admin
from django.utils.html import format_html
from .models import RadiusServer, RadiusAuthLog, RadiusAccounting, RadiusClient


@admin.register(RadiusServer)
class RadiusServerAdmin(admin.ModelAdmin):
    """Admin interface for RadiusServer model"""
    list_display = ['name', 'host', 'auth_port', 'acct_port', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'host']
    readonly_fields = ['created_at', 'updated_at', 'secret_status']
    ordering = ['name']

    fieldsets = (
        ('Server Info', {
            # SECURITY: secret field removed from direct display
            'fields': ('name', 'host', 'auth_port', 'acct_port', 'secret_status'),
            'description': 'Le secret RADIUS n\'est jamais affiché pour des raisons de sécurité.'
        }),
        ('Modifier le secret', {
            'fields': ('secret',),
            'classes': ('collapse',),
            'description': 'Entrez un nouveau secret uniquement si vous souhaitez le modifier.'
        }),
        ('Settings', {
            'fields': ('is_active', 'timeout', 'retries')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def secret_status(self, obj):
        """Indique si le secret est configuré sans l'afficher"""
        if obj.secret:
            return format_html('<span style="color: green;">✓ Configuré (non affiché)</span>')
        return format_html('<span style="color: red;">✗ Non configuré</span>')
    secret_status.short_description = 'Secret RADIUS'


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

    # Fix N+1 queries
    list_select_related = ['server', 'user']

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

    # Fix N+1 queries
    list_select_related = ['server', 'user']

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
    readonly_fields = ['created_at', 'updated_at', 'secret_status']
    ordering = ['name']

    fieldsets = (
        ('Client Info', {
            # SECURITY: secret field removed from direct display
            'fields': ('name', 'shortname', 'nas_type', 'ip_address', 'secret_status'),
            'description': 'Le secret NAS n\'est jamais affiché pour des raisons de sécurité.'
        }),
        ('Modifier le secret', {
            'fields': ('secret',),
            'classes': ('collapse',),
        }),
        ('Additional Info', {
            'fields': ('description', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def secret_status(self, obj):
        """Indique si le secret NAS est configuré"""
        if obj.secret:
            return format_html('<span style="color: green;">✓ Configuré (non affiché)</span>')
        return format_html('<span style="color: red;">✗ Non configuré</span>')
    secret_status.short_description = 'Secret NAS'

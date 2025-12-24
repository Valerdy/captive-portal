from django.contrib import admin
from django.utils.html import format_html
from .models import MikrotikRouter, MikrotikHotspotUser, MikrotikActiveConnection, MikrotikLog


@admin.register(MikrotikRouter)
class MikrotikRouterAdmin(admin.ModelAdmin):
    """Admin interface for MikrotikRouter model"""
    list_display = ['name', 'host', 'port', 'username', 'is_active', 'created_at']
    list_filter = ['is_active', 'use_ssl', 'created_at']
    search_fields = ['name', 'host', 'username', 'description']
    readonly_fields = ['created_at', 'updated_at', 'password_status']
    ordering = ['name']

    fieldsets = (
        ('Router Info', {
            # SECURITY: password field removed from display, use write-only
            'fields': ('name', 'host', 'port', 'username', 'password_status'),
            'description': 'Le mot de passe n\'est jamais affiché pour des raisons de sécurité.'
        }),
        ('Modifier le mot de passe', {
            'fields': ('password',),
            'classes': ('collapse',),
            'description': 'Entrez un nouveau mot de passe uniquement si vous souhaitez le modifier.'
        }),
        ('Settings', {
            'fields': ('use_ssl', 'is_active', 'description')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def password_status(self, obj):
        """Indique si le mot de passe est configuré sans l'afficher"""
        if obj.password:
            return format_html('<span style="color: green;">✓ Configuré (non affiché)</span>')
        return format_html('<span style="color: red;">✗ Non configuré</span>')
    password_status.short_description = 'Mot de passe'


@admin.register(MikrotikHotspotUser)
class MikrotikHotspotUserAdmin(admin.ModelAdmin):
    """Admin interface for MikrotikHotspotUser model"""
    list_display = [
        'username', 'router', 'user', 'mac_address', 'ip_address',
        'is_active', 'is_disabled', 'created_at'
    ]
    list_filter = ['is_active', 'is_disabled', 'router', 'created_at']
    search_fields = ['username', 'mac_address', 'ip_address', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'last_sync', 'password_status']
    ordering = ['-created_at']

    # Fix N+1 queries
    list_select_related = ['router', 'user']

    fieldsets = (
        ('User Info', {
            # SECURITY: password field removed from display
            'fields': ('router', 'user', 'username', 'password_status', 'mac_address', 'ip_address')
        }),
        ('Modifier le mot de passe', {
            'fields': ('password',),
            'classes': ('collapse',),
        }),
        ('Limits', {
            'fields': ('uptime_limit', 'bytes_in_limit', 'bytes_out_limit', 'rate_limit')
        }),
        ('Status', {
            'fields': ('is_active', 'is_disabled')
        }),
        ('Tracking', {
            'fields': ('created_at', 'updated_at', 'last_sync'),
            'classes': ('collapse',)
        }),
    )

    def password_status(self, obj):
        """Indique si le mot de passe est configuré"""
        if obj.password:
            return format_html('<span style="color: green;">✓ Configuré</span>')
        return format_html('<span style="color: red;">✗ Non configuré</span>')
    password_status.short_description = 'Mot de passe'


@admin.register(MikrotikActiveConnection)
class MikrotikActiveConnectionAdmin(admin.ModelAdmin):
    """Admin interface for MikrotikActiveConnection model"""
    list_display = [
        'session_id', 'username', 'router', 'ip_address',
        'mac_address', 'uptime', 'login_time'
    ]
    list_filter = ['router', 'login_time']
    search_fields = ['session_id', 'username', 'mac_address', 'ip_address']
    readonly_fields = ['last_update']
    ordering = ['-login_time']

    # Fix N+1 queries
    list_select_related = ['router', 'hotspot_user']

    fieldsets = (
        ('Connection Info', {
            'fields': ('router', 'hotspot_user', 'session_id', 'username', 'mac_address', 'ip_address')
        }),
        ('Statistics', {
            'fields': ('uptime', 'bytes_in', 'bytes_out', 'packets_in', 'packets_out')
        }),
        ('Timestamps', {
            'fields': ('login_time', 'last_update')
        }),
    )


@admin.register(MikrotikLog)
class MikrotikLogAdmin(admin.ModelAdmin):
    """Admin interface for MikrotikLog model"""
    list_display = ['router', 'level', 'operation', 'message', 'created_at']
    list_filter = ['level', 'operation', 'router', 'created_at']
    search_fields = ['operation', 'message', 'router__name']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Log Info', {
            'fields': ('router', 'level', 'operation', 'message', 'details')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )

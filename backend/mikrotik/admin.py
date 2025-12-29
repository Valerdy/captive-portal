from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta
from .models import MikrotikRouter, MikrotikHotspotUser, MikrotikActiveConnection, MikrotikLog


# =============================================================================
# Filtre personnalisé pour les dates
# =============================================================================

class CreatedAtDateRangeFilter(SimpleListFilter):
    """Filtre par plage de dates pour created_at"""
    title = 'Période'
    parameter_name = 'date_range'

    def lookups(self, request, model_admin):
        return [
            ('today', "Aujourd'hui"),
            ('yesterday', 'Hier'),
            ('week', 'Cette semaine'),
            ('month', 'Ce mois'),
        ]

    def queryset(self, request, queryset):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        if self.value() == 'today':
            return queryset.filter(created_at__gte=today_start)
        elif self.value() == 'yesterday':
            yesterday_start = today_start - timedelta(days=1)
            return queryset.filter(
                created_at__gte=yesterday_start,
                created_at__lt=today_start
            )
        elif self.value() == 'week':
            week_start = today_start - timedelta(days=7)
            return queryset.filter(created_at__gte=week_start)
        elif self.value() == 'month':
            month_start = today_start - timedelta(days=30)
            return queryset.filter(created_at__gte=month_start)
        return queryset


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
    """Admin interface for MikrotikLog model with pagination"""
    list_display = ['router', 'level_display', 'operation', 'message_truncated', 'created_at']
    list_filter = ['level', 'operation', 'router', CreatedAtDateRangeFilter, 'created_at']
    search_fields = ['operation', 'message', 'router__name']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    # Pagination améliorée pour éviter les problèmes de performance
    list_per_page = 50
    list_max_show_all = 200
    show_full_result_count = False  # Évite COUNT(*) coûteux sur grandes tables

    # Fix N+1 queries
    list_select_related = ['router']

    # Hiérarchie de dates pour navigation rapide
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Log Info', {
            'fields': ('router', 'level', 'operation', 'message', 'details')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )

    def level_display(self, obj):
        """Affiche le niveau avec indicateur visuel"""
        colors = {
            'info': '#17a2b8',
            'warning': '#ffc107',
            'error': '#dc3545',
            'debug': '#6c757d',
        }
        color = colors.get(obj.level, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_level_display()
        )
    level_display.short_description = 'Niveau'
    level_display.admin_order_field = 'level'

    def message_truncated(self, obj):
        """Affiche le message tronqué avec tooltip"""
        if len(obj.message) > 80:
            return format_html(
                '<span title="{}">{}&hellip;</span>',
                obj.message, obj.message[:80]
            )
        return obj.message
    message_truncated.short_description = 'Message'

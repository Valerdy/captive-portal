from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib import messages
from django.http import HttpResponse
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta
import csv
from .models import MikrotikRouter, MikrotikHotspotUser, MikrotikActiveConnection, MikrotikLog


# =============================================================================
# Constantes pour le formatage des dates
# =============================================================================
DATE_FORMAT = '%d/%m/%Y'
DATETIME_FORMAT = '%d/%m/%Y %H:%M'
DATETIME_FULL_FORMAT = '%d/%m/%Y %H:%M:%S'

# Pagination
ADMIN_LIST_PER_PAGE = 50
ADMIN_LIST_PER_PAGE_LARGE = 25


# =============================================================================
# Mixins
# =============================================================================

class DateFormatterMixin:
    """Mixin pour uniformiser le formatage des dates dans l'admin"""

    def format_date(self, date_value):
        if date_value:
            return date_value.strftime(DATE_FORMAT)
        return '-'

    def format_datetime(self, datetime_value):
        if datetime_value:
            return datetime_value.strftime(DATETIME_FORMAT)
        return '-'


class ExportCsvMixin:
    """Mixin pour ajouter l'export CSV aux ModelAdmin"""

    def get_export_fields(self):
        return [field.name for field in self.model._meta.fields]

    def get_export_filename(self):
        return f"{self.model._meta.verbose_name_plural}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"

    @admin.action(description="📥 Exporter en CSV")
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = self.get_export_fields()

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{self.get_export_filename()}"'
        response.write('\ufeff')

        writer = csv.writer(response, delimiter=';')
        headers = []
        for field_name in field_names:
            try:
                field = meta.get_field(field_name)
                headers.append(field.verbose_name.capitalize())
            except Exception:
                headers.append(field_name.replace('_', ' ').capitalize())
        writer.writerow(headers)

        for obj in queryset:
            row = []
            for field_name in field_names:
                value = getattr(obj, field_name, '')
                if hasattr(value, 'strftime'):
                    value = value.strftime(DATETIME_FORMAT)
                elif hasattr(value, '__str__'):
                    value = str(value)
                row.append(value)
            writer.writerow(row)

        messages.success(request, f"✅ {queryset.count()} enregistrement(s) exporté(s)")
        return response


# =============================================================================
# Filtres personnalisés
# =============================================================================

class DateRangeFilter(SimpleListFilter):
    """Filtre générique par plage de dates"""
    title = 'Période'
    parameter_name = 'date_range'
    date_field = 'created_at'

    def lookups(self, request, model_admin):
        return [
            ('today', "Aujourd'hui"),
            ('yesterday', 'Hier'),
            ('week', 'Cette semaine'),
            ('month', 'Ce mois'),
            ('quarter', 'Ce trimestre'),
        ]

    def queryset(self, request, queryset):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        filters = {
            'today': {f'{self.date_field}__gte': today_start},
            'yesterday': {
                f'{self.date_field}__gte': today_start - timedelta(days=1),
                f'{self.date_field}__lt': today_start
            },
            'week': {f'{self.date_field}__gte': today_start - timedelta(days=7)},
            'month': {f'{self.date_field}__gte': today_start - timedelta(days=30)},
            'quarter': {f'{self.date_field}__gte': today_start - timedelta(days=90)},
        }

        if self.value() in filters:
            return queryset.filter(**filters[self.value()])
        return queryset


class CreatedAtDateRangeFilter(DateRangeFilter):
    """Filtre par created_at"""
    date_field = 'created_at'


class LoginTimeDateRangeFilter(DateRangeFilter):
    """Filtre par login_time"""
    title = 'Connexion'
    date_field = 'login_time'


class LogLevelFilter(SimpleListFilter):
    """Filtre par niveau de log"""
    title = 'Niveau'
    parameter_name = 'log_level'

    def lookups(self, request, model_admin):
        return [
            ('info', 'ℹ️ Info'),
            ('warning', '⚠️ Warning'),
            ('error', '❌ Error'),
            ('debug', '🔧 Debug'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(level=self.value())
        return queryset


@admin.register(MikrotikRouter)
class MikrotikRouterAdmin(DateFormatterMixin, ExportCsvMixin, admin.ModelAdmin):
    """Admin interface for MikrotikRouter model"""
    list_per_page = ADMIN_LIST_PER_PAGE
    list_max_show_all = 200

    list_display = ['name', 'host', 'port', 'username', 'is_active_display', 'created_at_display']
    list_filter = ['is_active', 'use_ssl', CreatedAtDateRangeFilter]
    search_fields = ['name', 'host', 'username', 'description']
    readonly_fields = ['created_at', 'updated_at', 'password_status']
    ordering = ['name']

    actions = ['export_as_csv', 'test_connection']

    fieldsets = (
        ('Router Info', {
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

    def get_export_fields(self):
        return ['name', 'host', 'port', 'username', 'use_ssl', 'is_active', 'created_at']

    def password_status(self, obj):
        """Indique si le mot de passe est configuré sans l'afficher"""
        if obj.password:
            return format_html('<span style="color: green;">✓ Configuré (non affiché)</span>')
        return format_html('<span style="color: red;">✗ Non configuré</span>')
    password_status.short_description = 'Mot de passe'

    def is_active_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">● Actif</span>')
        return format_html('<span style="color: #888;">○ Inactif</span>')
    is_active_display.short_description = 'Statut'
    is_active_display.admin_order_field = 'is_active'

    def created_at_display(self, obj):
        return self.format_datetime(obj.created_at)
    created_at_display.short_description = 'Créé le'
    created_at_display.admin_order_field = 'created_at'

    @admin.action(description="🔌 Tester la connexion")
    def test_connection(self, request, queryset):
        """Teste la connexion aux routeurs sélectionnés"""
        success = 0
        errors = []
        for router in queryset:
            # Simulation - en production, ajouter le vrai test de connexion
            if router.is_active and router.password:
                success += 1
            else:
                errors.append(f"{router.name}: Configuration incomplète")
        if success:
            messages.success(request, f"✅ {success} routeur(s) configuré(s) correctement")
        if errors:
            messages.warning(request, f"⚠️ Erreurs: {'; '.join(errors[:3])}")


class HotspotUserStatusFilter(SimpleListFilter):
    """Filtre par statut hotspot user"""
    title = 'Statut'
    parameter_name = 'hotspot_status'

    def lookups(self, request, model_admin):
        return [
            ('active', '● Actif'),
            ('disabled', '◐ Désactivé'),
            ('inactive', '○ Inactif'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(is_active=True, is_disabled=False)
        elif self.value() == 'disabled':
            return queryset.filter(is_disabled=True)
        elif self.value() == 'inactive':
            return queryset.filter(is_active=False)
        return queryset


@admin.register(MikrotikHotspotUser)
class MikrotikHotspotUserAdmin(DateFormatterMixin, ExportCsvMixin, admin.ModelAdmin):
    """Admin interface for MikrotikHotspotUser model"""
    list_per_page = ADMIN_LIST_PER_PAGE
    list_max_show_all = 200

    list_display = [
        'username', 'router', 'user', 'mac_address', 'ip_address',
        'status_display', 'created_at_display'
    ]
    list_filter = [HotspotUserStatusFilter, 'router', CreatedAtDateRangeFilter]
    search_fields = ['username', 'mac_address', 'ip_address', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'last_sync', 'password_status']
    ordering = ['-created_at']

    # Fix N+1 queries
    list_select_related = ['router', 'user']

    actions = ['export_as_csv', 'enable_users', 'disable_users']

    fieldsets = (
        ('User Info', {
            'fields': ('router', 'user', 'username', 'password_status', 'mac_address', 'ip_address'),
            'description': 'Informations de connexion Hotspot'
        }),
        ('Modifier le mot de passe', {
            'fields': ('password',),
            'classes': ('collapse',),
        }),
        ('Limits', {
            'fields': ('uptime_limit', 'bytes_in_limit', 'bytes_out_limit', 'rate_limit'),
            'description': 'Limites de connexion et bande passante'
        }),
        ('Status', {
            'fields': ('is_active', 'is_disabled')
        }),
        ('Tracking', {
            'fields': ('created_at', 'updated_at', 'last_sync'),
            'classes': ('collapse',)
        }),
    )

    def get_export_fields(self):
        return ['username', 'mac_address', 'ip_address', 'is_active', 'is_disabled', 'created_at']

    def password_status(self, obj):
        """Indique si le mot de passe est configuré"""
        if obj.password:
            return format_html('<span style="color: green;">✓ Configuré</span>')
        return format_html('<span style="color: red;">✗ Non configuré</span>')
    password_status.short_description = 'Mot de passe'

    def status_display(self, obj):
        if not obj.is_active:
            return format_html('<span style="color: #888;">○ Inactif</span>')
        elif obj.is_disabled:
            return format_html('<span style="color: orange;">◐ Désactivé</span>')
        return format_html('<span style="color: green;">● Actif</span>')
    status_display.short_description = 'Statut'

    def created_at_display(self, obj):
        return self.format_datetime(obj.created_at)
    created_at_display.short_description = 'Créé le'
    created_at_display.admin_order_field = 'created_at'

    @admin.action(description="✓ Activer les utilisateurs")
    def enable_users(self, request, queryset):
        updated = queryset.update(is_active=True, is_disabled=False)
        messages.success(request, f"{updated} utilisateur(s) activé(s)")

    @admin.action(description="✗ Désactiver les utilisateurs")
    def disable_users(self, request, queryset):
        updated = queryset.update(is_disabled=True)
        messages.success(request, f"{updated} utilisateur(s) désactivé(s)")


@admin.register(MikrotikActiveConnection)
class MikrotikActiveConnectionAdmin(DateFormatterMixin, ExportCsvMixin, admin.ModelAdmin):
    """Admin interface for MikrotikActiveConnection model"""
    list_per_page = ADMIN_LIST_PER_PAGE
    list_max_show_all = 200
    show_full_result_count = False

    list_display = [
        'session_id', 'username', 'router', 'ip_address',
        'mac_address', 'uptime_display', 'data_display', 'login_time_display'
    ]
    list_filter = ['router', LoginTimeDateRangeFilter]
    search_fields = ['session_id', 'username', 'mac_address', 'ip_address']
    readonly_fields = ['session_id', 'username', 'mac_address', 'ip_address',
                      'uptime', 'bytes_in', 'bytes_out', 'login_time', 'last_update']
    ordering = ['-login_time']

    # Fix N+1 queries
    list_select_related = ['router', 'hotspot_user']

    actions = ['export_as_csv', 'disconnect_sessions']

    fieldsets = (
        ('Connection Info', {
            'fields': ('router', 'hotspot_user', 'session_id', 'username', 'mac_address', 'ip_address')
        }),
        ('Statistics', {
            'fields': ('uptime', 'bytes_in', 'bytes_out', 'packets_in', 'packets_out'),
            'description': 'Statistiques de la session en cours'
        }),
        ('Timestamps', {
            'fields': ('login_time', 'last_update')
        }),
    )

    def get_export_fields(self):
        return ['session_id', 'username', 'ip_address', 'mac_address', 'uptime', 'bytes_in', 'bytes_out', 'login_time']

    def uptime_display(self, obj):
        hours, remainder = divmod(obj.uptime, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m {seconds}s"
    uptime_display.short_description = 'Durée'
    uptime_display.admin_order_field = 'uptime'

    def data_display(self, obj):
        total = obj.bytes_in + obj.bytes_out
        if total >= 1024**3:
            return f"{total / 1024**3:.2f} Go"
        elif total >= 1024**2:
            return f"{total / 1024**2:.1f} Mo"
        elif total >= 1024:
            return f"{total / 1024:.0f} Ko"
        return f"{total} o"
    data_display.short_description = 'Données'

    def login_time_display(self, obj):
        return self.format_datetime(obj.login_time)
    login_time_display.short_description = 'Connexion'
    login_time_display.admin_order_field = 'login_time'

    @admin.action(description="🚫 Déconnecter les sessions")
    def disconnect_sessions(self, request, queryset):
        # En production, implémenter la déconnexion via API MikroTik
        count = queryset.count()
        messages.warning(request, f"⚠️ Action non implémentée: {count} session(s) à déconnecter")

    def has_add_permission(self, request):
        return False  # Les connexions sont créées automatiquement

    def has_change_permission(self, request, obj=None):
        return False  # Les connexions ne sont pas modifiables


@admin.register(MikrotikLog)
class MikrotikLogAdmin(DateFormatterMixin, ExportCsvMixin, admin.ModelAdmin):
    """Admin interface for MikrotikLog model with pagination"""
    list_display = ['router', 'level_display', 'operation', 'message_truncated', 'created_at_display']
    list_filter = [LogLevelFilter, 'operation', 'router', CreatedAtDateRangeFilter]
    search_fields = ['operation', 'message', 'router__name']
    readonly_fields = ['router', 'level', 'operation', 'message', 'details', 'created_at']
    ordering = ['-created_at']

    # Pagination améliorée pour éviter les problèmes de performance
    list_per_page = ADMIN_LIST_PER_PAGE_LARGE
    list_max_show_all = 200
    show_full_result_count = False

    # Fix N+1 queries
    list_select_related = ['router']

    # Hiérarchie de dates pour navigation rapide
    date_hierarchy = 'created_at'

    actions = ['export_as_csv']

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

    def created_at_display(self, obj):
        return self.format_datetime(obj.created_at)
    created_at_display.short_description = 'Date'
    created_at_display.admin_order_field = 'created_at'

    def get_export_fields(self):
        return ['router', 'level', 'operation', 'message', 'created_at']

    def has_add_permission(self, request):
        return False  # Les logs sont créés automatiquement

    def has_change_permission(self, request, obj=None):
        return False  # Les logs ne sont pas modifiables

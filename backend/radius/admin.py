from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib import messages
from django.http import HttpResponse
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta
import csv
from .models import (
    RadiusServer, RadiusAuthLog, RadiusAccounting, RadiusClient,
    RadCheck, RadReply, RadUserGroup, RadGroupCheck, RadGroupReply, RadPostAuth
)


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
    date_field = 'timestamp'

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


class TimestampDateRangeFilter(DateRangeFilter):
    """Filtre par timestamp"""
    date_field = 'timestamp'


class AuthDateRangeFilter(DateRangeFilter):
    """Filtre par authdate"""
    title = "Date d'auth"
    date_field = 'authdate'


class CreatedAtDateRangeFilter(DateRangeFilter):
    """Filtre par created_at"""
    date_field = 'created_at'


class AuthStatusFilter(SimpleListFilter):
    """Filtre par statut d'authentification"""
    title = 'Résultat'
    parameter_name = 'auth_status'

    def lookups(self, request, model_admin):
        return [
            ('accept', '✓ Accepté'),
            ('reject', '✗ Rejeté'),
            ('challenge', '? Challenge'),
            ('error', '⚠ Erreur'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class AccountingStatusFilter(SimpleListFilter):
    """Filtre par type d'accounting"""
    title = 'Type'
    parameter_name = 'acct_type'

    def lookups(self, request, model_admin):
        return [
            ('start', '▶ Start'),
            ('stop', '⏹ Stop'),
            ('interim-update', '🔄 Interim'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status_type=self.value())
        return queryset


class RadCheckStatusFilter(SimpleListFilter):
    """Filtre par statut radcheck"""
    title = 'Statut'
    parameter_name = 'radcheck_status'

    def lookups(self, request, model_admin):
        return [
            ('active', '● Actif'),
            ('disabled', '○ Désactivé'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(statut=True)
        elif self.value() == 'disabled':
            return queryset.filter(statut=False)
        return queryset


class PostAuthReplyFilter(SimpleListFilter):
    """Filtre par résultat post-auth"""
    title = 'Résultat'
    parameter_name = 'reply'

    def lookups(self, request, model_admin):
        return [
            ('Access-Accept', '✓ Accept'),
            ('Access-Reject', '✗ Reject'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(reply=self.value())
        return queryset


# =============================================================================
# Admin Classes
# =============================================================================

@admin.register(RadiusServer)
class RadiusServerAdmin(DateFormatterMixin, ExportCsvMixin, admin.ModelAdmin):
    """Admin interface for RadiusServer model"""
    list_per_page = ADMIN_LIST_PER_PAGE
    list_max_show_all = 200

    list_display = ['name', 'host', 'auth_port', 'acct_port', 'is_active_display', 'created_at_display']
    list_filter = ['is_active', CreatedAtDateRangeFilter]
    search_fields = ['name', 'host']
    readonly_fields = ['created_at', 'updated_at', 'secret_status']
    ordering = ['name']

    actions = ['export_as_csv', 'test_connection']

    fieldsets = (
        ('Server Info', {
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

    def get_export_fields(self):
        return ['name', 'host', 'auth_port', 'acct_port', 'is_active', 'timeout', 'retries', 'created_at']

    def secret_status(self, obj):
        if obj.secret:
            return format_html('<span style="color: green;">✓ Configuré (non affiché)</span>')
        return format_html('<span style="color: red;">✗ Non configuré</span>')
    secret_status.short_description = 'Secret RADIUS'

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
        success = 0
        for server in queryset.filter(is_active=True):
            if server.secret:
                success += 1
        messages.success(request, f"✅ {success} serveur(s) configuré(s) correctement")


@admin.register(RadiusAuthLog)
class RadiusAuthLogAdmin(DateFormatterMixin, ExportCsvMixin, admin.ModelAdmin):
    """Admin interface for RadiusAuthLog model"""
    list_per_page = ADMIN_LIST_PER_PAGE_LARGE
    list_max_show_all = 200
    show_full_result_count = False

    list_display = [
        'username', 'server', 'status_display', 'ip_address',
        'mac_address', 'nas_ip_address', 'timestamp_display'
    ]
    list_filter = [AuthStatusFilter, 'server', TimestampDateRangeFilter]
    search_fields = ['username', 'ip_address', 'mac_address', 'nas_ip_address', 'user__email']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'

    list_select_related = ['server', 'user']

    actions = ['export_as_csv']

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

    def get_export_fields(self):
        return ['username', 'status', 'ip_address', 'mac_address', 'nas_ip_address', 'timestamp']

    def status_display(self, obj):
        colors = {'accept': 'green', 'reject': 'red', 'challenge': 'orange', 'error': '#dc3545'}
        icons = {'accept': '✓', 'reject': '✗', 'challenge': '?', 'error': '⚠'}
        color = colors.get(obj.status, '#888')
        icon = icons.get(obj.status, '?')
        return format_html('<span style="color: {};">{} {}</span>', color, icon, obj.get_status_display())
    status_display.short_description = 'Statut'
    status_display.admin_order_field = 'status'

    def timestamp_display(self, obj):
        return self.format_datetime(obj.timestamp)
    timestamp_display.short_description = 'Date'
    timestamp_display.admin_order_field = 'timestamp'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(RadiusAccounting)
class RadiusAccountingAdmin(DateFormatterMixin, ExportCsvMixin, admin.ModelAdmin):
    """Admin interface for RadiusAccounting model"""
    list_per_page = ADMIN_LIST_PER_PAGE_LARGE
    list_max_show_all = 200
    show_full_result_count = False

    list_display = [
        'session_id', 'username', 'status_type_display', 'framed_ip_address',
        'session_time_display', 'total_octets_display', 'timestamp_display'
    ]
    list_filter = [AccountingStatusFilter, 'termination_cause', 'server', TimestampDateRangeFilter]
    search_fields = ['session_id', 'username', 'framed_ip_address', 'mac_address']
    readonly_fields = ['timestamp', 'total_octets']
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'

    list_select_related = ['server', 'user']

    actions = ['export_as_csv']

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
            'fields': ('session_time', 'start_time', 'stop_time'),
            'description': 'Durée et timestamps de la session'
        }),
        ('Data Usage', {
            'fields': (
                'input_octets', 'output_octets', 'input_packets', 'output_packets',
                'input_gigawords', 'output_gigawords', 'total_octets'
            ),
            'description': 'Données transférées en octets'
        }),
        ('Raw Data', {
            'fields': ('raw_data',),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
    )

    def get_export_fields(self):
        return ['session_id', 'username', 'status_type', 'framed_ip_address',
                'session_time', 'input_octets', 'output_octets', 'timestamp']

    def status_type_display(self, obj):
        icons = {'start': '▶', 'stop': '⏹', 'interim-update': '🔄'}
        icon = icons.get(obj.status_type, '?')
        return format_html('{} {}', icon, obj.get_status_type_display())
    status_type_display.short_description = 'Type'
    status_type_display.admin_order_field = 'status_type'

    def session_time_display(self, obj):
        if obj.session_time:
            hours, remainder = divmod(obj.session_time, 3600)
            minutes, _ = divmod(remainder, 60)
            if hours > 0:
                return f"{hours}h {minutes}m"
            return f"{minutes}m"
        return '-'
    session_time_display.short_description = 'Durée'
    session_time_display.admin_order_field = 'session_time'

    def total_octets_display(self, obj):
        total = obj.total_octets
        if total >= 1024**3:
            return f"{total / 1024**3:.2f} Go"
        elif total >= 1024**2:
            return f"{total / 1024**2:.1f} Mo"
        elif total >= 1024:
            return f"{total / 1024:.0f} Ko"
        return f"{total} o"
    total_octets_display.short_description = 'Données'

    def timestamp_display(self, obj):
        return self.format_datetime(obj.timestamp)
    timestamp_display.short_description = 'Date'
    timestamp_display.admin_order_field = 'timestamp'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(RadiusClient)
class RadiusClientAdmin(DateFormatterMixin, ExportCsvMixin, admin.ModelAdmin):
    """Admin interface for RadiusClient model"""
    list_per_page = ADMIN_LIST_PER_PAGE
    list_max_show_all = 200

    list_display = ['name', 'shortname', 'ip_address', 'nas_type', 'is_active_display', 'created_at_display']
    list_filter = ['is_active', 'nas_type', CreatedAtDateRangeFilter]
    search_fields = ['name', 'shortname', 'ip_address', 'description']
    readonly_fields = ['created_at', 'updated_at', 'secret_status']
    ordering = ['name']

    actions = ['export_as_csv', 'activate_clients', 'deactivate_clients']

    fieldsets = (
        ('Client Info', {
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

    def get_export_fields(self):
        return ['name', 'shortname', 'ip_address', 'nas_type', 'is_active', 'created_at']

    def secret_status(self, obj):
        if obj.secret:
            return format_html('<span style="color: green;">✓ Configuré (non affiché)</span>')
        return format_html('<span style="color: red;">✗ Non configuré</span>')
    secret_status.short_description = 'Secret NAS'

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

    @admin.action(description="✓ Activer les clients")
    def activate_clients(self, request, queryset):
        updated = queryset.update(is_active=True)
        messages.success(request, f"{updated} client(s) activé(s)")

    @admin.action(description="✗ Désactiver les clients")
    def deactivate_clients(self, request, queryset):
        updated = queryset.update(is_active=False)
        messages.success(request, f"{updated} client(s) désactivé(s)")


# =============================================================================
# Tables FreeRADIUS
# =============================================================================

@admin.register(RadCheck)
class RadCheckAdmin(DateFormatterMixin, ExportCsvMixin, admin.ModelAdmin):
    """Admin pour la table radcheck de FreeRADIUS"""
    list_per_page = ADMIN_LIST_PER_PAGE
    list_max_show_all = 200

    list_display = ['username', 'attribute', 'op', 'value_display', 'statut_display', 'quota_display']
    list_filter = ['attribute', RadCheckStatusFilter, 'op']
    search_fields = ['username', 'attribute', 'value']
    ordering = ['username', 'attribute']

    actions = ['export_as_csv', 'enable_users', 'disable_users']

    fieldsets = (
        ('Utilisateur', {
            'fields': ('username',)
        }),
        ('Attribut RADIUS', {
            'fields': ('attribute', 'op', 'value'),
            'description': 'Attributs vérifiés avant authentification'
        }),
        ('Statut & Quota', {
            'fields': ('statut', 'quota'),
            'description': 'Champs personnalisés ajoutés par le captive portal'
        }),
    )

    def get_export_fields(self):
        return ['username', 'attribute', 'op', 'statut', 'quota']

    def value_display(self, obj):
        if obj.attribute == 'Cleartext-Password':
            return format_html('<span style="color: #888;">••••••••</span>')
        return obj.value[:50] if obj.value else '-'
    value_display.short_description = 'Valeur'

    def statut_display(self, obj):
        if obj.statut:
            return format_html('<span style="color: green;">✓ Actif</span>')
        return format_html('<span style="color: red;">✗ Inactif</span>')
    statut_display.short_description = 'Statut'
    statut_display.admin_order_field = 'statut'

    def quota_display(self, obj):
        if obj.quota:
            quota_gb = obj.quota / (1024 ** 3)
            return f"{quota_gb:.2f} Go"
        return '-'
    quota_display.short_description = 'Quota'

    @admin.action(description="✓ Activer les utilisateurs")
    def enable_users(self, request, queryset):
        updated = queryset.update(statut=True)
        messages.success(request, f"{updated} utilisateur(s) activé(s)")

    @admin.action(description="✗ Désactiver les utilisateurs")
    def disable_users(self, request, queryset):
        updated = queryset.update(statut=False)
        messages.success(request, f"{updated} utilisateur(s) désactivé(s)")


@admin.register(RadReply)
class RadReplyAdmin(ExportCsvMixin, admin.ModelAdmin):
    """Admin pour la table radreply de FreeRADIUS"""
    list_per_page = ADMIN_LIST_PER_PAGE
    list_max_show_all = 200

    list_display = ['username', 'attribute', 'op', 'value_display']
    list_filter = ['attribute', 'op']
    search_fields = ['username', 'attribute', 'value']
    ordering = ['username', 'attribute']

    actions = ['export_as_csv']

    fieldsets = (
        ('Utilisateur', {
            'fields': ('username',)
        }),
        ('Attribut RADIUS', {
            'fields': ('attribute', 'op', 'value'),
            'description': 'Attributs envoyés dans Access-Accept au NAS'
        }),
    )

    def get_export_fields(self):
        return ['username', 'attribute', 'op', 'value']

    def value_display(self, obj):
        if len(obj.value) > 50:
            return format_html('<span title="{}">{}&hellip;</span>', obj.value, obj.value[:50])
        return obj.value
    value_display.short_description = 'Valeur'


@admin.register(RadUserGroup)
class RadUserGroupAdmin(ExportCsvMixin, admin.ModelAdmin):
    """Admin pour la table radusergroup de FreeRADIUS"""
    list_per_page = ADMIN_LIST_PER_PAGE
    list_max_show_all = 200

    list_display = ['username', 'groupname', 'priority']
    list_filter = ['groupname', 'priority']
    search_fields = ['username', 'groupname']
    ordering = ['groupname', 'priority', 'username']

    actions = ['export_as_csv']

    def get_export_fields(self):
        return ['username', 'groupname', 'priority']


@admin.register(RadGroupCheck)
class RadGroupCheckAdmin(ExportCsvMixin, admin.ModelAdmin):
    """Admin pour la table radgroupcheck de FreeRADIUS"""
    list_per_page = ADMIN_LIST_PER_PAGE
    list_max_show_all = 200

    list_display = ['groupname', 'attribute', 'op', 'value']
    list_filter = ['groupname', 'attribute']
    search_fields = ['groupname', 'attribute', 'value']
    ordering = ['groupname', 'attribute']

    actions = ['export_as_csv']

    def get_export_fields(self):
        return ['groupname', 'attribute', 'op', 'value']


@admin.register(RadGroupReply)
class RadGroupReplyAdmin(ExportCsvMixin, admin.ModelAdmin):
    """Admin pour la table radgroupreply de FreeRADIUS"""
    list_per_page = ADMIN_LIST_PER_PAGE
    list_max_show_all = 200

    list_display = ['groupname', 'attribute', 'op', 'value_display']
    list_filter = ['groupname', 'attribute']
    search_fields = ['groupname', 'attribute', 'value']
    ordering = ['groupname', 'attribute']

    actions = ['export_as_csv']

    def get_export_fields(self):
        return ['groupname', 'attribute', 'op', 'value']

    def value_display(self, obj):
        if len(obj.value) > 50:
            return format_html('<span title="{}">{}&hellip;</span>', obj.value, obj.value[:50])
        return obj.value
    value_display.short_description = 'Valeur'


@admin.register(RadPostAuth)
class RadPostAuthAdmin(DateFormatterMixin, ExportCsvMixin, admin.ModelAdmin):
    """Admin pour la table radpostauth de FreeRADIUS"""
    list_per_page = ADMIN_LIST_PER_PAGE_LARGE
    list_max_show_all = 200
    show_full_result_count = False

    list_display = ['username', 'reply_display', 'authdate_display']
    list_filter = [PostAuthReplyFilter, AuthDateRangeFilter]
    search_fields = ['username']
    readonly_fields = ['username', 'pass_field', 'reply', 'authdate']
    ordering = ['-authdate']
    date_hierarchy = 'authdate'

    actions = ['export_as_csv']

    fieldsets = (
        ('Authentification', {
            'fields': ('username', 'pass_field', 'reply', 'authdate')
        }),
    )

    def get_export_fields(self):
        return ['username', 'reply', 'authdate']

    def reply_display(self, obj):
        if obj.reply == 'Access-Accept':
            return format_html('<span style="color: green;">✓ Accept</span>')
        elif obj.reply == 'Access-Reject':
            return format_html('<span style="color: red;">✗ Reject</span>')
        return obj.reply
    reply_display.short_description = 'Résultat'
    reply_display.admin_order_field = 'reply'

    def authdate_display(self, obj):
        return self.format_datetime(obj.authdate)
    authdate_display.short_description = 'Date'
    authdate_display.admin_order_field = 'authdate'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

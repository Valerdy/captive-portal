from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta
from .models import (
    RadiusServer, RadiusAuthLog, RadiusAccounting, RadiusClient,
    RadCheck, RadReply, RadUserGroup, RadGroupCheck, RadGroupReply, RadPostAuth
)


# =============================================================================
# Filtres personnalisés pour les dates
# =============================================================================

class DateRangeFilter(SimpleListFilter):
    """Filtre par plage de dates récentes"""
    title = 'Période'
    parameter_name = 'date_range'

    def lookups(self, request, model_admin):
        return [
            ('today', "Aujourd'hui"),
            ('yesterday', 'Hier'),
            ('week', 'Cette semaine'),
            ('month', 'Ce mois'),
            ('older', 'Plus ancien'),
        ]

    def queryset(self, request, queryset):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        if self.value() == 'today':
            return queryset.filter(**{f'{self.date_field}__gte': today_start})
        elif self.value() == 'yesterday':
            yesterday_start = today_start - timedelta(days=1)
            return queryset.filter(
                **{f'{self.date_field}__gte': yesterday_start,
                   f'{self.date_field}__lt': today_start}
            )
        elif self.value() == 'week':
            week_start = today_start - timedelta(days=7)
            return queryset.filter(**{f'{self.date_field}__gte': week_start})
        elif self.value() == 'month':
            month_start = today_start - timedelta(days=30)
            return queryset.filter(**{f'{self.date_field}__gte': month_start})
        elif self.value() == 'older':
            month_start = today_start - timedelta(days=30)
            return queryset.filter(**{f'{self.date_field}__lt': month_start})
        return queryset


class TimestampDateRangeFilter(DateRangeFilter):
    """Filtre par date pour champ 'timestamp'"""
    date_field = 'timestamp'


class AuthDateRangeFilter(DateRangeFilter):
    """Filtre par date pour champ 'authdate'"""
    date_field = 'authdate'


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
    list_filter = ['status', 'server', TimestampDateRangeFilter, 'timestamp']
    search_fields = ['username', 'ip_address', 'mac_address', 'nas_ip_address']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']
    list_per_page = 50  # Pagination améliorée

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


# =============================================================================
# Tables FreeRADIUS (radcheck, radreply, radusergroup, etc.)
# =============================================================================

@admin.register(RadCheck)
class RadCheckAdmin(admin.ModelAdmin):
    """
    Admin pour la table radcheck de FreeRADIUS.

    Cette table contient les attributs de vérification (authentication):
    - Cleartext-Password: mot de passe
    - Simultaneous-Use: limite de connexions simultanées
    - Max-Total-Octets: quota total (si utilisé ici)
    """
    list_display = ['username', 'attribute', 'op', 'value_display', 'statut_display', 'quota_display']
    list_filter = ['attribute', 'statut', 'op']
    search_fields = ['username', 'attribute', 'value']
    ordering = ['username', 'attribute']
    list_per_page = 50

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

    def value_display(self, obj):
        """Masque les mots de passe dans l'affichage"""
        if obj.attribute == 'Cleartext-Password':
            return format_html('<span style="color: #888;">••••••••</span>')
        return obj.value[:50] if obj.value else '-'
    value_display.short_description = 'Valeur'

    def statut_display(self, obj):
        """Affiche le statut avec indicateur visuel"""
        if obj.statut:
            return format_html('<span style="color: green;">✓ Actif</span>')
        return format_html('<span style="color: red;">✗ Inactif</span>')
    statut_display.short_description = 'Statut'
    statut_display.admin_order_field = 'statut'

    def quota_display(self, obj):
        """Affiche le quota en Go si défini"""
        if obj.quota:
            quota_gb = obj.quota / (1024 ** 3)
            return f"{quota_gb:.2f} Go"
        return '-'
    quota_display.short_description = 'Quota'


@admin.register(RadReply)
class RadReplyAdmin(admin.ModelAdmin):
    """
    Admin pour la table radreply de FreeRADIUS.

    Cette table contient les attributs envoyés dans Access-Accept:
    - Mikrotik-Rate-Limit: bande passante
    - Session-Timeout: durée max de session
    - Idle-Timeout: délai d'inactivité
    - ChilliSpot-Max-Total-Octets: quota
    """
    list_display = ['username', 'attribute', 'op', 'value']
    list_filter = ['attribute', 'op']
    search_fields = ['username', 'attribute', 'value']
    ordering = ['username', 'attribute']
    list_per_page = 50

    fieldsets = (
        ('Utilisateur', {
            'fields': ('username',)
        }),
        ('Attribut RADIUS', {
            'fields': ('attribute', 'op', 'value'),
            'description': 'Attributs envoyés dans Access-Accept au NAS'
        }),
    )


@admin.register(RadUserGroup)
class RadUserGroupAdmin(admin.ModelAdmin):
    """
    Admin pour la table radusergroup de FreeRADIUS.

    Associe les utilisateurs aux groupes RADIUS.
    """
    list_display = ['username', 'groupname', 'priority']
    list_filter = ['groupname', 'priority']
    search_fields = ['username', 'groupname']
    ordering = ['groupname', 'priority', 'username']
    list_per_page = 50


@admin.register(RadGroupCheck)
class RadGroupCheckAdmin(admin.ModelAdmin):
    """
    Admin pour la table radgroupcheck de FreeRADIUS.

    Attributs de vérification au niveau du groupe.
    """
    list_display = ['groupname', 'attribute', 'op', 'value']
    list_filter = ['groupname', 'attribute']
    search_fields = ['groupname', 'attribute', 'value']
    ordering = ['groupname', 'attribute']
    list_per_page = 50


@admin.register(RadGroupReply)
class RadGroupReplyAdmin(admin.ModelAdmin):
    """
    Admin pour la table radgroupreply de FreeRADIUS.

    Attributs de réponse au niveau du groupe.
    """
    list_display = ['groupname', 'attribute', 'op', 'value']
    list_filter = ['groupname', 'attribute']
    search_fields = ['groupname', 'attribute', 'value']
    ordering = ['groupname', 'attribute']
    list_per_page = 50


@admin.register(RadPostAuth)
class RadPostAuthAdmin(admin.ModelAdmin):
    """
    Admin pour la table radpostauth de FreeRADIUS.

    Journal des authentifications (post-auth).
    Note: La table standard radpostauth ne contient que username, pass, reply, authdate.
    """
    list_display = ['username', 'reply', 'authdate']
    list_filter = ['reply', AuthDateRangeFilter, 'authdate']
    search_fields = ['username']
    readonly_fields = ['authdate']
    ordering = ['-authdate']
    list_per_page = 50
    date_hierarchy = 'authdate'

    fieldsets = (
        ('Authentification', {
            'fields': ('username', 'pass_field', 'reply', 'authdate')
        }),
    )

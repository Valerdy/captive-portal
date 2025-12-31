from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.admin import SimpleListFilter
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.utils.html import format_html
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from datetime import timedelta
import csv
from .models import (
    User, Device, Session, Voucher, Promotion, Profile,
    UserProfileUsage, ProfileHistory, ProfileAlert, BlockedSite
)
from .security import csrf_protect_admin_action


# =============================================================================
# Constantes pour le formatage des dates
# =============================================================================
DATE_FORMAT = '%d/%m/%Y'
DATETIME_FORMAT = '%d/%m/%Y %H:%M'
DATETIME_FULL_FORMAT = '%d/%m/%Y %H:%M:%S'


# =============================================================================
# Mixins pour fonctionnalités réutilisables
# =============================================================================

class DateFormatterMixin:
    """Mixin pour uniformiser le formatage des dates dans l'admin"""

    def format_date(self, date_value):
        """Formate une date en dd/mm/yyyy"""
        if date_value:
            return date_value.strftime(DATE_FORMAT)
        return '-'

    def format_datetime(self, datetime_value):
        """Formate une date/heure en dd/mm/yyyy HH:MM"""
        if datetime_value:
            return datetime_value.strftime(DATETIME_FORMAT)
        return '-'

    def format_datetime_full(self, datetime_value):
        """Formate une date/heure complète avec secondes"""
        if datetime_value:
            return datetime_value.strftime(DATETIME_FULL_FORMAT)
        return '-'


class ExportCsvMixin:
    """Mixin pour ajouter l'export CSV aux ModelAdmin"""

    def get_export_fields(self):
        """Retourne les champs à exporter. À surcharger dans les sous-classes."""
        return [field.name for field in self.model._meta.fields]

    def get_export_filename(self):
        """Retourne le nom du fichier d'export"""
        return f"{self.model._meta.verbose_name_plural}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"

    @admin.action(description="📥 Exporter en CSV")
    def export_as_csv(self, request, queryset):
        """Exporte les objets sélectionnés en CSV"""
        meta = self.model._meta
        field_names = self.get_export_fields()

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{self.get_export_filename()}"'
        response.write('\ufeff')  # BOM UTF-8 pour Excel

        writer = csv.writer(response, delimiter=';')
        # En-têtes avec verbose_name
        headers = []
        for field_name in field_names:
            try:
                field = meta.get_field(field_name)
                headers.append(field.verbose_name.capitalize())
            except Exception:
                headers.append(field_name.replace('_', ' ').capitalize())
        writer.writerow(headers)

        # Données
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

        self.message_user(
            request,
            f"✅ {queryset.count()} enregistrement(s) exporté(s)",
            messages.SUCCESS
        )
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
            ('year', 'Cette année'),
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
            'year': {f'{self.date_field}__gte': today_start - timedelta(days=365)},
        }

        if self.value() in filters:
            return queryset.filter(**filters[self.value()])
        return queryset


class CreatedAtDateRangeFilter(DateRangeFilter):
    """Filtre par created_at"""
    date_field = 'created_at'


class DateJoinedDateRangeFilter(DateRangeFilter):
    """Filtre par date d'inscription"""
    title = "Date d'inscription"
    date_field = 'date_joined'


class StartTimeDateRangeFilter(DateRangeFilter):
    """Filtre par start_time"""
    title = 'Date de session'
    date_field = 'start_time'


class AddedDateRangeFilter(DateRangeFilter):
    """Filtre par added_date"""
    title = 'Date d\'ajout'
    date_field = 'added_date'


class QuotaStatusFilter(SimpleListFilter):
    """Filtre par statut de quota"""
    title = 'Statut quota'
    parameter_name = 'quota_status'

    def lookups(self, request, model_admin):
        return [
            ('exceeded', 'Quota dépassé'),
            ('warning', 'Quota > 80%'),
            ('ok', 'Quota OK'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'exceeded':
            return queryset.filter(is_exceeded=True)
        elif self.value() == 'warning':
            # Filtre complexe basé sur les propriétés
            return queryset.filter(is_exceeded=False)
        elif self.value() == 'ok':
            return queryset.filter(is_exceeded=False)
        return queryset


class RadiusStatusFilter(SimpleListFilter):
    """Filtre par statut RADIUS utilisateur"""
    title = 'Statut RADIUS'
    parameter_name = 'radius_status'

    def lookups(self, request, model_admin):
        return [
            ('active', '● Actif (activé + enabled)'),
            ('disabled', '◐ Désactivé (activé mais disabled)'),
            ('pending', '○ En attente (non activé)'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(is_radius_activated=True, is_radius_enabled=True)
        elif self.value() == 'disabled':
            return queryset.filter(is_radius_activated=True, is_radius_enabled=False)
        elif self.value() == 'pending':
            return queryset.filter(is_radius_activated=False)
        return queryset


class ProfileQuotaTypeFilter(SimpleListFilter):
    """Filtre par type de quota du profil"""
    title = 'Type de quota'
    parameter_name = 'profile_quota'

    def lookups(self, request, model_admin):
        return [
            ('limited', 'Limité'),
            ('unlimited', 'Illimité'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(quota_type=self.value())
        return queryset


class SyncStatusFilter(SimpleListFilter):
    """Filtre par statut de synchronisation"""
    title = 'Statut sync'
    parameter_name = 'sync'

    def lookups(self, request, model_admin):
        return [
            ('synced', '✓ Synchronisé'),
            ('pending', '⏳ En attente'),
            ('error', '✗ Erreur'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(sync_status=self.value())
        return queryset


# =============================================================================
# FIX #16: Pagination Configuration for Admin Lists
# =============================================================================
# Django defaults to 100 items per page. For large tables, we configure
# appropriate limits to prevent timeout and memory issues.

ADMIN_LIST_PER_PAGE = 50  # Default for most models
ADMIN_LIST_PER_PAGE_LARGE = 25  # For models with heavy relations


# =============================================================================
# Inlines pour les relations
# =============================================================================

class DeviceInline(admin.TabularInline):
    """Inline pour les appareils de l'utilisateur"""
    model = Device
    extra = 0
    max_num = 10
    readonly_fields = ['mac_address', 'ip_address', 'device_type', 'first_seen', 'last_seen']
    fields = ['mac_address', 'ip_address', 'device_type', 'is_active', 'first_seen', 'last_seen']
    show_change_link = True
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class SessionInline(admin.TabularInline):
    """Inline pour les sessions récentes de l'utilisateur"""
    model = Session
    extra = 0
    max_num = 5
    readonly_fields = ['session_id', 'ip_address', 'mac_address', 'status', 'start_time', 'total_bytes']
    fields = ['session_id', 'ip_address', 'status', 'start_time', 'total_bytes']
    ordering = ['-start_time']
    show_change_link = True
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class ProfileAlertInline(admin.TabularInline):
    """Inline pour les alertes d'un profil"""
    model = ProfileAlert
    extra = 0
    max_num = 5
    fields = ['alert_type', 'threshold_percent', 'threshold_days', 'notification_method', 'is_active']
    show_change_link = True


class BlockedSiteInline(admin.TabularInline):
    """Inline pour les sites bloqués d'un profil"""
    model = BlockedSite
    fk_name = 'profile'
    extra = 0
    max_num = 10
    fields = ['domain', 'category', 'is_active', 'sync_status']
    readonly_fields = ['sync_status']
    show_change_link = True


@admin.register(User)
class UserAdmin(DateFormatterMixin, ExportCsvMixin, BaseUserAdmin):
    """Admin interface for User model with RADIUS management actions"""

    # Fix #16: Pagination explicite pour éviter timeout sur grandes listes
    list_per_page = ADMIN_LIST_PER_PAGE
    list_max_show_all = 200  # Limite pour "Show all"

    list_display = [
        'username', 'email', 'first_name', 'last_name',
        'promotion', 'profile', 'radius_status_display',
        'phone_number', 'is_active', 'date_joined_display'
    ]
    list_filter = [
        'is_active', 'is_staff', 'is_voucher_user',
        RadiusStatusFilter,  # Filtre personnalisé RADIUS
        DateJoinedDateRangeFilter,  # Filtre par période d'inscription
        'promotion', 'profile'
    ]
    search_fields = [
        'username', 'email', 'first_name', 'last_name',
        'phone_number', 'mac_address', 'matricule', 'ip_address',
        'promotion__name', 'profile__name', 'voucher_code'
    ]
    ordering = ['-date_joined']
    autocomplete_fields = ['promotion', 'profile']
    date_hierarchy = 'date_joined'

    # Fix N+1 queries: prefetch FK relations for list view
    list_select_related = ['promotion', 'profile']

    # Inlines pour voir les appareils et sessions
    inlines = [DeviceInline, SessionInline]

    # Actions RADIUS pour gestion en masse + Export
    actions = [
        'activate_radius', 'deactivate_radius',
        'resync_radius', 'enable_radius', 'disable_radius',
        'export_as_csv'
    ]

    def get_export_fields(self):
        return ['username', 'email', 'first_name', 'last_name',
                'phone_number', 'matricule', 'is_active',
                'is_radius_activated', 'is_radius_enabled', 'date_joined']

    def date_joined_display(self, obj):
        """Affiche la date d'inscription formatée"""
        return self.format_datetime(obj.date_joined)
    date_joined_display.short_description = "Date d'inscription"
    date_joined_display.admin_order_field = 'date_joined'

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Captive Portal Info', {
            'fields': ('promotion', 'profile', 'matricule', 'phone_number', 'mac_address', 'ip_address', 'is_voucher_user', 'voucher_code')
        }),
        ('RADIUS Status', {
            # Note: cleartext_password nécessaire pour l'activation RADIUS (table radcheck)
            'fields': ('is_radius_activated', 'is_radius_enabled', 'cleartext_password'),
            'classes': ('collapse',),
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Captive Portal Info', {
            'fields': ('promotion', 'profile', 'matricule', 'phone_number', 'mac_address', 'ip_address', 'is_voucher_user', 'voucher_code')
        }),
    )

    def radius_status_display(self, obj):
        """Affiche le statut RADIUS avec indicateur visuel"""
        if not obj.is_radius_activated:
            return format_html('<span style="color: #888;">○ Non activé</span>')
        elif obj.is_radius_enabled:
            return format_html('<span style="color: green;">● Actif</span>')
        else:
            return format_html('<span style="color: orange;">◐ Désactivé</span>')
    radius_status_display.short_description = 'RADIUS'
    radius_status_display.admin_order_field = 'is_radius_enabled'

    @admin.action(description="🔓 Activer RADIUS (première activation)")
    @csrf_protect_admin_action
    def activate_radius(self, request, queryset):
        """Active RADIUS pour les utilisateurs sélectionnés (première activation)"""
        from radius.services import ProfileRadiusService

        activated = 0
        errors = []

        for user in queryset.filter(is_radius_activated=False):
            if not user.cleartext_password:
                errors.append(f"{user.username}: mot de passe requis")
                continue

            profile = user.get_effective_profile()
            if not profile:
                errors.append(f"{user.username}: aucun profil")
                continue

            result = ProfileRadiusService.activate_user_radius(user, activated_by=request.user)
            if result.get('success'):
                activated += 1
            else:
                errors.append(f"{user.username}: {result.get('error')}")

        if activated:
            messages.success(request, f"{activated} utilisateur(s) activé(s) dans RADIUS")
        if errors:
            messages.warning(request, f"Erreurs: {'; '.join(errors[:5])}")

    @admin.action(description="🔒 Désactiver RADIUS (supprime les entrées)")
    @csrf_protect_admin_action
    def deactivate_radius(self, request, queryset):
        """Désactive complètement RADIUS pour les utilisateurs sélectionnés"""
        from radius.services import ProfileRadiusService

        deactivated = 0
        for user in queryset.filter(is_radius_activated=True):
            result = ProfileRadiusService.deactivate_user_radius(
                user, reason='admin_bulk', deactivated_by=request.user
            )
            if result.get('success'):
                deactivated += 1

        messages.success(request, f"{deactivated} utilisateur(s) désactivé(s) de RADIUS")

    @admin.action(description="🔄 Resynchroniser RADIUS")
    @csrf_protect_admin_action
    def resync_radius(self, request, queryset):
        """Resynchronise les attributs RADIUS pour les utilisateurs sélectionnés"""
        from radius.services import ProfileRadiusService

        synced = 0
        errors = []

        for user in queryset.filter(is_radius_activated=True):
            profile = user.get_effective_profile()
            if not profile:
                errors.append(f"{user.username}: aucun profil")
                continue

            try:
                ProfileRadiusService.sync_user_to_radius(user, profile)
                synced += 1
            except Exception as e:
                errors.append(f"{user.username}: {str(e)[:30]}")

        if synced:
            messages.success(request, f"{synced} utilisateur(s) resynchronisé(s)")
        if errors:
            messages.warning(request, f"Erreurs: {'; '.join(errors[:5])}")

    @admin.action(description="✓ Activer accès (is_radius_enabled=True)")
    def enable_radius(self, request, queryset):
        """Active l'accès RADIUS sans resynchroniser"""
        updated = queryset.filter(is_radius_activated=True).update(is_radius_enabled=True)
        messages.success(request, f"{updated} utilisateur(s) activé(s)")

    @admin.action(description="✗ Désactiver accès (is_radius_enabled=False)")
    def disable_radius(self, request, queryset):
        """Désactive temporairement l'accès RADIUS"""
        updated = queryset.filter(is_radius_activated=True).update(is_radius_enabled=False)
        messages.success(request, f"{updated} utilisateur(s) désactivé(s)")


class PromotionBlockedSiteInline(admin.TabularInline):
    """Inline pour les sites bloqués d'une promotion"""
    model = BlockedSite
    fk_name = 'promotion'
    extra = 0
    max_num = 10
    fields = ['domain', 'category', 'is_active', 'sync_status']
    readonly_fields = ['sync_status']
    show_change_link = True


@admin.register(Promotion)
class PromotionAdmin(DateFormatterMixin, ExportCsvMixin, admin.ModelAdmin):
    # Fix #16: Pagination
    list_per_page = ADMIN_LIST_PER_PAGE
    list_max_show_all = 200

    list_display = ['name', 'profile', 'is_active', 'user_count_display', 'created_at_display', 'updated_at_display']
    list_filter = ['is_active', 'profile', CreatedAtDateRangeFilter]
    search_fields = ['name', 'description', 'profile__name', 'users__username']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']
    autocomplete_fields = ['profile']
    list_select_related = ['profile']
    inlines = [PromotionBlockedSiteInline]
    actions = ['export_as_csv']

    fieldsets = (
        ('Informations', {
            'fields': ('name', 'profile', 'is_active'),
            'description': 'Informations de base de la promotion'
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_export_fields(self):
        return ['name', 'is_active', 'created_at', 'updated_at']

    def user_count_display(self, obj):
        """Affiche le nombre d'utilisateurs dans la promotion"""
        count = obj.users.count()
        return format_html('<span title="{} utilisateur(s)">{}</span>', count, count)
    user_count_display.short_description = 'Utilisateurs'

    def created_at_display(self, obj):
        return self.format_datetime(obj.created_at)
    created_at_display.short_description = 'Créé le'
    created_at_display.admin_order_field = 'created_at'

    def updated_at_display(self, obj):
        return self.format_datetime(obj.updated_at)
    updated_at_display.short_description = 'Modifié le'
    updated_at_display.admin_order_field = 'updated_at'


@admin.register(Profile)
class ProfileAdmin(DateFormatterMixin, ExportCsvMixin, admin.ModelAdmin):
    """Admin interface for Profile model with RADIUS synchronization actions"""

    # Fix #16: Pagination
    list_per_page = ADMIN_LIST_PER_PAGE
    list_max_show_all = 200

    list_display = [
        'name', 'quota_type', 'data_volume_display',
        'bandwidth_display', 'validity_duration', 'is_active',
        'radius_status_display', 'created_at_display'
    ]
    list_filter = [
        'is_active', 'is_radius_enabled',
        ProfileQuotaTypeFilter,  # Filtre personnalisé
        'validity_duration',
        CreatedAtDateRangeFilter
    ]
    search_fields = ['name', 'description', 'radius_group_name', 'promotions__name']
    ordering = ['name']
    readonly_fields = [
        'created_at', 'updated_at',
        'data_volume_gb', 'bandwidth_upload_mbps', 'bandwidth_download_mbps',
        'daily_limit_gb', 'weekly_limit_gb', 'monthly_limit_gb',
        'radius_group_name', 'last_radius_sync', 'radius_sync_status'
    ]

    # Inlines pour alertes et sites bloqués
    inlines = [ProfileAlertInline, BlockedSiteInline]

    # Actions RADIUS pour gestion en masse + Export
    actions = [
        'enable_radius_sync', 'disable_radius_sync',
        'force_sync_to_radius', 'remove_from_radius',
        'export_as_csv'
    ]

    def get_export_fields(self):
        return ['name', 'quota_type', 'data_volume', 'bandwidth_upload',
                'bandwidth_download', 'validity_duration', 'is_active',
                'is_radius_enabled', 'created_at']

    def created_at_display(self, obj):
        return self.format_datetime(obj.created_at)
    created_at_display.short_description = 'Créé le'
    created_at_display.admin_order_field = 'created_at'

    fieldsets = (
        ('Informations de base', {
            'fields': ('name', 'description', 'is_active', 'created_by')
        }),
        ('Synchronisation RADIUS', {
            'fields': (
                'is_radius_enabled', 'radius_group_name',
                'last_radius_sync', 'radius_sync_status'
            ),
            'description': (
                'Contrôle la synchronisation vers FreeRADIUS (radgroupreply). '
                'Activez "is_radius_enabled" pour synchroniser ce profil vers RADIUS.'
            )
        }),
        ('Bande passante', {
            'fields': ('bandwidth_upload', 'bandwidth_upload_mbps', 'bandwidth_download', 'bandwidth_download_mbps'),
            'description': 'Bande passante en Mbps (ex: 10 = 10 Mbps). Format MikroTik: downloadM/uploadM'
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

    def radius_status_display(self, obj):
        """Affiche le statut de synchronisation RADIUS avec indicateur visuel"""
        if not obj.is_active:
            return format_html('<span style="color: #888;">○ Inactif</span>')
        elif not obj.is_radius_enabled:
            return format_html('<span style="color: #888;">○ RADIUS désactivé</span>')
        elif obj.is_synced_to_radius:
            return format_html(
                '<span style="color: green;" title="Groupe: {}">● Synchronisé</span>',
                obj.radius_group_name
            )
        else:
            return format_html('<span style="color: orange;">◐ En attente</span>')
    radius_status_display.short_description = 'RADIUS'
    radius_status_display.admin_order_field = 'is_radius_enabled'

    @admin.action(description="🔓 Activer sync RADIUS (is_radius_enabled=True)")
    def enable_radius_sync(self, request, queryset):
        """
        Active la synchronisation RADIUS pour les profils sélectionnés.
        Déclenche automatiquement la synchronisation via le signal post_save.
        """
        synced = 0
        errors = []

        for profile in queryset.filter(is_active=True):
            try:
                profile.is_radius_enabled = True
                profile.save()  # Déclenche le signal post_save
                synced += 1
            except Exception as e:
                errors.append(f"{profile.name}: {str(e)[:50]}")

        if synced:
            messages.success(
                request,
                f"✅ {synced} profil(s) activé(s) dans RADIUS"
            )
        if errors:
            messages.warning(request, f"Erreurs: {'; '.join(errors[:3])}")

        # Profils inactifs ignorés
        inactive = queryset.filter(is_active=False).count()
        if inactive:
            messages.info(
                request,
                f"ℹ️ {inactive} profil(s) inactif(s) ignoré(s)"
            )

    @admin.action(description="🔒 Désactiver sync RADIUS (is_radius_enabled=False)")
    def disable_radius_sync(self, request, queryset):
        """
        Désactive la synchronisation RADIUS pour les profils sélectionnés.
        Supprime les entrées radgroupreply correspondantes.
        """
        disabled = 0
        errors = []

        for profile in queryset.filter(is_radius_enabled=True):
            try:
                profile.is_radius_enabled = False
                profile.save()  # Déclenche le signal qui supprime de radgroupreply
                disabled += 1
            except Exception as e:
                errors.append(f"{profile.name}: {str(e)[:50]}")

        if disabled:
            messages.success(
                request,
                f"🔒 {disabled} profil(s) désactivé(s) de RADIUS"
            )
        if errors:
            messages.warning(request, f"Erreurs: {'; '.join(errors[:3])}")

    @admin.action(description="🔄 Forcer synchronisation RADIUS")
    def force_sync_to_radius(self, request, queryset):
        """
        Force la resynchronisation des profils sélectionnés vers RADIUS.
        Utile après modification manuelle de la base radgroupreply.
        """
        synced = 0
        errors = []

        for profile in queryset.filter(is_active=True, is_radius_enabled=True):
            try:
                result = profile.sync_to_radius()
                if result.get('success'):
                    synced += 1
                else:
                    errors.append(f"{profile.name}: {result.get('error')}")
            except Exception as e:
                errors.append(f"{profile.name}: {str(e)[:50]}")

        if synced:
            messages.success(
                request,
                f"🔄 {synced} profil(s) resynchronisé(s) vers RADIUS"
            )
        if errors:
            messages.warning(request, f"Erreurs: {'; '.join(errors[:3])}")

        # Profils non éligibles
        not_eligible = queryset.exclude(is_active=True, is_radius_enabled=True).count()
        if not_eligible:
            messages.info(
                request,
                f"ℹ️ {not_eligible} profil(s) ignoré(s) (inactif ou RADIUS désactivé)"
            )

    @admin.action(description="🗑️ Supprimer de RADIUS (conserve le profil Django)")
    def remove_from_radius(self, request, queryset):
        """
        Supprime les entrées radgroupreply des profils sélectionnés.
        Ne supprime pas le profil Django, seulement les données RADIUS.
        """
        removed = 0
        errors = []

        # Filter profiles that are synced (have radius_group_name set)
        for profile in queryset.filter(radius_group_name__isnull=False):
            try:
                result = profile.remove_from_radius()
                if result.get('success'):
                    removed += 1
                else:
                    errors.append(f"{profile.name}: {result.get('error')}")
            except Exception as e:
                errors.append(f"{profile.name}: {str(e)[:50]}")

        if removed:
            messages.success(
                request,
                f"🗑️ {removed} profil(s) supprimé(s) de RADIUS"
            )
        if errors:
            messages.warning(request, f"Erreurs: {'; '.join(errors[:3])}")


class FirstSeenDateRangeFilter(DateRangeFilter):
    """Filtre par first_seen"""
    title = 'Première connexion'
    date_field = 'first_seen'


class LastSeenDateRangeFilter(DateRangeFilter):
    """Filtre par last_seen"""
    title = 'Dernière activité'
    date_field = 'last_seen'


@admin.register(Device)
class DeviceAdmin(DateFormatterMixin, ExportCsvMixin, admin.ModelAdmin):
    """Admin interface for Device model"""
    # Fix #16: Pagination
    list_per_page = ADMIN_LIST_PER_PAGE
    list_max_show_all = 200

    list_display = [
        'mac_address', 'user', 'ip_address', 'device_type',
        'is_active', 'first_seen_display', 'last_seen_display'
    ]
    list_filter = ['is_active', 'device_type', FirstSeenDateRangeFilter, LastSeenDateRangeFilter]
    search_fields = ['mac_address', 'ip_address', 'hostname', 'user__username', 'user__email', 'user_agent']
    readonly_fields = ['first_seen', 'last_seen', 'user_agent']
    ordering = ['-last_seen']
    date_hierarchy = 'first_seen'

    # Fix N+1 queries
    list_select_related = ['user']

    actions = ['export_as_csv', 'deactivate_devices']

    fieldsets = (
        ('Appareil', {
            'fields': ('user', 'mac_address', 'ip_address', 'hostname', 'device_type', 'is_active')
        }),
        ('Informations techniques', {
            'fields': ('user_agent',),
            'classes': ('collapse',)
        }),
        ('Historique', {
            'fields': ('first_seen', 'last_seen'),
            'classes': ('collapse',)
        }),
    )

    def get_export_fields(self):
        return ['mac_address', 'ip_address', 'hostname', 'device_type', 'is_active', 'first_seen', 'last_seen']

    def first_seen_display(self, obj):
        return self.format_datetime(obj.first_seen)
    first_seen_display.short_description = 'Première connexion'
    first_seen_display.admin_order_field = 'first_seen'

    def last_seen_display(self, obj):
        return self.format_datetime(obj.last_seen)
    last_seen_display.short_description = 'Dernière activité'
    last_seen_display.admin_order_field = 'last_seen'

    @admin.action(description="🚫 Désactiver les appareils sélectionnés")
    def deactivate_devices(self, request, queryset):
        updated = queryset.update(is_active=False)
        messages.success(request, f"{updated} appareil(s) désactivé(s)")


class SessionStatusFilter(SimpleListFilter):
    """Filtre par statut de session"""
    title = 'Statut'
    parameter_name = 'session_status'

    def lookups(self, request, model_admin):
        return [
            ('active', '● Active'),
            ('expired', '○ Expirée'),
            ('terminated', '✗ Terminée'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


@admin.register(Session)
class SessionAdmin(DateFormatterMixin, ExportCsvMixin, admin.ModelAdmin):
    """Admin interface for Session model"""
    # Fix #16: Pagination - Sessions can be very large
    list_per_page = ADMIN_LIST_PER_PAGE_LARGE
    list_max_show_all = 100
    show_full_result_count = False  # Performance sur grandes tables

    list_display = [
        'session_id', 'user', 'ip_address', 'mac_address',
        'status_display', 'start_time_display', 'total_bytes_display'
    ]
    list_filter = [SessionStatusFilter, StartTimeDateRangeFilter]
    search_fields = ['session_id', 'user__username', 'user__email', 'ip_address', 'mac_address', 'device__hostname']
    readonly_fields = ['created_at', 'updated_at', 'start_time', 'is_expired', 'total_bytes']
    ordering = ['-start_time']
    date_hierarchy = 'start_time'

    # Fix N+1 queries
    list_select_related = ['user', 'device']

    actions = ['export_as_csv', 'terminate_sessions']

    fieldsets = (
        ('Session Info', {
            'fields': ('user', 'device', 'session_id', 'ip_address', 'mac_address', 'status')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time', 'timeout_duration', 'is_expired')
        }),
        ('Data Usage', {
            'fields': ('bytes_in', 'bytes_out', 'packets_in', 'packets_out', 'total_bytes'),
            'description': 'Données transférées en octets'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_export_fields(self):
        return ['session_id', 'ip_address', 'mac_address', 'status', 'start_time', 'bytes_in', 'bytes_out']

    def status_display(self, obj):
        colors = {'active': 'green', 'expired': '#888', 'terminated': 'red'}
        icons = {'active': '●', 'expired': '○', 'terminated': '✗'}
        color = colors.get(obj.status, '#888')
        icon = icons.get(obj.status, '?')
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    status_display.short_description = 'Statut'
    status_display.admin_order_field = 'status'

    def start_time_display(self, obj):
        return self.format_datetime(obj.start_time)
    start_time_display.short_description = 'Début'
    start_time_display.admin_order_field = 'start_time'

    def total_bytes_display(self, obj):
        total = obj.total_bytes
        if total >= 1024**3:
            return f"{total / 1024**3:.2f} Go"
        elif total >= 1024**2:
            return f"{total / 1024**2:.2f} Mo"
        elif total >= 1024:
            return f"{total / 1024:.2f} Ko"
        return f"{total} o"
    total_bytes_display.short_description = 'Données transférées'

    @admin.action(description="⏹️ Terminer les sessions sélectionnées")
    def terminate_sessions(self, request, queryset):
        updated = queryset.filter(status='active').update(status='terminated', end_time=timezone.now())
        messages.success(request, f"{updated} session(s) terminée(s)")


class VoucherStatusFilter(SimpleListFilter):
    """Filtre par statut de voucher"""
    title = 'Statut'
    parameter_name = 'voucher_status'

    def lookups(self, request, model_admin):
        return [
            ('active', '● Actif'),
            ('used', '◐ Utilisé'),
            ('expired', '○ Expiré'),
            ('revoked', '✗ Révoqué'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class ValidFromDateRangeFilter(DateRangeFilter):
    """Filtre par valid_from"""
    title = 'Valide depuis'
    date_field = 'valid_from'


class ValidUntilDateRangeFilter(DateRangeFilter):
    """Filtre par valid_until"""
    title = 'Valide jusqu\'à'
    date_field = 'valid_until'


@admin.register(Voucher)
class VoucherAdmin(DateFormatterMixin, ExportCsvMixin, admin.ModelAdmin):
    """Admin interface for Voucher model"""
    # Fix #16: Pagination
    list_per_page = ADMIN_LIST_PER_PAGE
    list_max_show_all = 200

    list_display = [
        'code', 'status_display', 'duration_display', 'max_devices', 'used_count',
        'valid_from_display', 'valid_until_display', 'created_by', 'is_valid_display'
    ]
    list_filter = [VoucherStatusFilter, ValidFromDateRangeFilter, ValidUntilDateRangeFilter, CreatedAtDateRangeFilter]
    search_fields = ['code', 'notes', 'created_by__username', 'used_by__username', 'used_by__email']
    readonly_fields = ['created_at', 'used_at', 'is_valid']
    ordering = ['-created_at']

    # Fix N+1 queries
    list_select_related = ['created_by', 'used_by']

    actions = ['export_as_csv', 'revoke_vouchers', 'extend_validity']

    fieldsets = (
        ('Voucher Info', {
            'fields': ('code', 'status', 'duration', 'max_devices', 'used_count'),
            'description': 'Informations de base du voucher'
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until', 'is_valid'),
            'description': 'Période de validité du voucher'
        }),
        ('Usage', {
            'fields': ('used_by', 'used_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'notes'),
            'classes': ('collapse',)
        }),
    )

    def get_export_fields(self):
        return ['code', 'status', 'duration', 'max_devices', 'used_count', 'valid_from', 'valid_until', 'created_at']

    def status_display(self, obj):
        colors = {'active': 'green', 'used': 'orange', 'expired': '#888', 'revoked': 'red'}
        icons = {'active': '●', 'used': '◐', 'expired': '○', 'revoked': '✗'}
        color = colors.get(obj.status, '#888')
        icon = icons.get(obj.status, '?')
        return format_html('<span style="color: {};">{} {}</span>', color, icon, obj.get_status_display())
    status_display.short_description = 'Statut'
    status_display.admin_order_field = 'status'

    def duration_display(self, obj):
        if obj.duration >= 3600:
            return f"{obj.duration // 3600}h"
        elif obj.duration >= 60:
            return f"{obj.duration // 60}min"
        return f"{obj.duration}s"
    duration_display.short_description = 'Durée'
    duration_display.admin_order_field = 'duration'

    def valid_from_display(self, obj):
        return self.format_datetime(obj.valid_from)
    valid_from_display.short_description = 'Valide depuis'
    valid_from_display.admin_order_field = 'valid_from'

    def valid_until_display(self, obj):
        return self.format_datetime(obj.valid_until)
    valid_until_display.short_description = 'Valide jusqu\'à'
    valid_until_display.admin_order_field = 'valid_until'

    def is_valid_display(self, obj):
        if obj.is_valid:
            return format_html('<span style="color: green;">✓ Valide</span>')
        return format_html('<span style="color: red;">✗ Invalide</span>')
    is_valid_display.short_description = 'Validité'
    is_valid_display.boolean = True

    @admin.action(description="❌ Révoquer les vouchers sélectionnés")
    def revoke_vouchers(self, request, queryset):
        """Révoque les vouchers sélectionnés (nécessite confirmation)"""
        updated = queryset.exclude(status='revoked').update(status='revoked')
        messages.success(request, f"{updated} voucher(s) révoqué(s)")

    @admin.action(description="📅 Prolonger la validité (+7 jours)")
    def extend_validity(self, request, queryset):
        """Prolonge la validité des vouchers de 7 jours"""
        from datetime import timedelta
        count = 0
        for voucher in queryset.filter(status='active'):
            voucher.valid_until = voucher.valid_until + timedelta(days=7)
            voucher.save()
            count += 1
        messages.success(request, f"{count} voucher(s) prolongé(s) de 7 jours")


class ActivationDateRangeFilter(DateRangeFilter):
    """Filtre par activation_date"""
    title = 'Date d\'activation'
    date_field = 'activation_date'


@admin.register(UserProfileUsage)
class UserProfileUsageAdmin(DateFormatterMixin, ExportCsvMixin, admin.ModelAdmin):
    """Admin interface for UserProfileUsage model"""
    list_per_page = ADMIN_LIST_PER_PAGE
    list_max_show_all = 200

    list_display = [
        'user', 'effective_profile_display', 'total_usage_gb_display',
        'daily_usage_display', 'is_exceeded_display', 'is_expired_display', 'is_active',
        'activation_date_display'
    ]
    list_filter = ['is_active', QuotaStatusFilter, ActivationDateRangeFilter]
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = [
        'used_today_gb', 'used_week_gb', 'used_month_gb', 'used_total_gb',
        'daily_usage_percent', 'weekly_usage_percent',
        'monthly_usage_percent', 'total_usage_percent',
        'last_daily_reset', 'last_weekly_reset', 'last_monthly_reset',
        'created_at', 'updated_at'
    ]
    autocomplete_fields = ['user']
    ordering = ['-created_at']

    # Fix N+1 queries
    list_select_related = ['user', 'user__profile', 'user__promotion', 'user__promotion__profile']

    actions = ['export_as_csv', 'reset_daily_usage', 'reset_all_usage']

    fieldsets = (
        ('Utilisateur', {
            'fields': ('user', 'is_active', 'activation_date')
        }),
        ('Consommation (octets)', {
            'fields': ('used_today', 'used_week', 'used_month', 'used_total'),
            'description': 'Données brutes en octets'
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

    def get_export_fields(self):
        return ['user', 'used_today', 'used_week', 'used_month', 'used_total',
                'is_exceeded', 'is_active', 'activation_date']

    def effective_profile_display(self, obj):
        """Affiche le profil effectif"""
        profile = obj.get_effective_profile()
        return profile.name if profile else "Aucun"
    effective_profile_display.short_description = 'Profil effectif'

    def total_usage_gb_display(self, obj):
        """Affiche la consommation totale en Go"""
        return f"{obj.used_total_gb} Go"
    total_usage_gb_display.short_description = 'Total consommé'

    def activation_date_display(self, obj):
        return self.format_datetime(obj.activation_date)
    activation_date_display.short_description = 'Activé le'
    activation_date_display.admin_order_field = 'activation_date'

    def is_exceeded_display(self, obj):
        if obj.is_exceeded:
            return format_html('<span style="color: red;">⚠️ Dépassé</span>')
        return format_html('<span style="color: green;">✓ OK</span>')
    is_exceeded_display.short_description = 'Quota'
    is_exceeded_display.admin_order_field = 'is_exceeded'

    @admin.action(description="🔄 Réinitialiser la consommation journalière")
    def reset_daily_usage(self, request, queryset):
        for usage in queryset:
            usage.reset_daily()
        messages.success(request, f"{queryset.count()} consommation(s) journalière(s) réinitialisée(s)")

    @admin.action(description="🔄 Réinitialiser toute la consommation")
    def reset_all_usage(self, request, queryset):
        for usage in queryset:
            usage.reset_all()
        messages.success(request, f"{queryset.count()} consommation(s) réinitialisée(s) complètement")

    def daily_usage_display(self, obj):
        """Affiche la consommation journalière avec pourcentage"""
        return f"{obj.used_today_gb} Go ({round(obj.daily_usage_percent, 1)}%)"
    daily_usage_display.short_description = 'Aujourd\'hui'

    def is_expired_display(self, obj):
        """Affiche si le profil est expiré"""
        return obj.is_expired()
    is_expired_display.boolean = True
    is_expired_display.short_description = 'Expiré'


class ChangedAtDateRangeFilter(DateRangeFilter):
    """Filtre par changed_at"""
    title = 'Date de changement'
    date_field = 'changed_at'


class ChangeTypeFilter(SimpleListFilter):
    """Filtre par type de changement"""
    title = 'Type de changement'
    parameter_name = 'change_type'

    def lookups(self, request, model_admin):
        return [
            ('assigned', '➕ Assignation'),
            ('updated', '🔄 Modification'),
            ('removed', '➖ Suppression'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(change_type=self.value())
        return queryset


@admin.register(ProfileHistory)
class ProfileHistoryAdmin(DateFormatterMixin, ExportCsvMixin, admin.ModelAdmin):
    """Admin interface for ProfileHistory model"""
    list_per_page = ADMIN_LIST_PER_PAGE
    list_max_show_all = 200

    list_display = [
        'user', 'change_type_display', 'old_profile', 'new_profile',
        'changed_by', 'changed_at_display'
    ]
    list_filter = [ChangeTypeFilter, ChangedAtDateRangeFilter]
    search_fields = [
        'user__username', 'user__email', 'old_profile__name',
        'new_profile__name', 'changed_by__username', 'reason'
    ]
    readonly_fields = ['user', 'change_type', 'old_profile', 'new_profile', 'changed_by', 'changed_at']
    autocomplete_fields = ['user', 'old_profile', 'new_profile', 'changed_by']
    ordering = ['-changed_at']
    date_hierarchy = 'changed_at'

    # Fix N+1 queries
    list_select_related = ['user', 'old_profile', 'new_profile', 'changed_by']

    actions = ['export_as_csv']

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

    def get_export_fields(self):
        return ['user', 'change_type', 'old_profile', 'new_profile', 'changed_by', 'changed_at', 'reason']

    def change_type_display(self, obj):
        icons = {'assigned': '➕', 'updated': '🔄', 'removed': '➖'}
        icon = icons.get(obj.change_type, '?')
        return format_html('{} {}', icon, obj.get_change_type_display())
    change_type_display.short_description = 'Type'
    change_type_display.admin_order_field = 'change_type'

    def changed_at_display(self, obj):
        return self.format_datetime(obj.changed_at)
    changed_at_display.short_description = 'Date'
    changed_at_display.admin_order_field = 'changed_at'

    def has_add_permission(self, request):
        return False  # Les historiques ne doivent pas être créés manuellement

    def has_change_permission(self, request, obj=None):
        return False  # Les historiques ne doivent pas être modifiés

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Seuls les superusers peuvent supprimer


class AlertTypeFilter(SimpleListFilter):
    """Filtre par type d'alerte"""
    title = "Type d'alerte"
    parameter_name = 'alert_type'

    def lookups(self, request, model_admin):
        return [
            ('quota_warning', '⚠️ Avertissement quota'),
            ('quota_critical', '🚨 Quota critique'),
            ('expiry_warning', '📅 Avertissement expiration'),
            ('expiry_imminent', '⏰ Expiration imminente'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(alert_type=self.value())
        return queryset


@admin.register(ProfileAlert)
class ProfileAlertAdmin(DateFormatterMixin, ExportCsvMixin, admin.ModelAdmin):
    """Admin interface for ProfileAlert model"""
    list_per_page = ADMIN_LIST_PER_PAGE
    list_max_show_all = 200

    list_display = [
        'profile', 'alert_type_display', 'threshold_percent',
        'threshold_days', 'notification_method_display', 'is_active_display',
        'created_at_display'
    ]
    list_filter = [AlertTypeFilter, 'notification_method', 'is_active', CreatedAtDateRangeFilter]
    search_fields = ['profile__name', 'message_template']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['profile', 'created_by']
    ordering = ['-created_at']

    # Fix N+1 queries
    list_select_related = ['profile', 'created_by']

    actions = ['export_as_csv', 'activate_alerts', 'deactivate_alerts']

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

    def get_export_fields(self):
        return ['profile', 'alert_type', 'threshold_percent', 'threshold_days',
                'notification_method', 'is_active', 'created_at']

    def alert_type_display(self, obj):
        icons = {
            'quota_warning': '⚠️',
            'quota_critical': '🚨',
            'expiry_warning': '📅',
            'expiry_imminent': '⏰'
        }
        icon = icons.get(obj.alert_type, '?')
        return format_html('{} {}', icon, obj.get_alert_type_display())
    alert_type_display.short_description = 'Type'
    alert_type_display.admin_order_field = 'alert_type'

    def notification_method_display(self, obj):
        icons = {'email': '📧', 'sms': '📱', 'system': '🔔', 'all': '📢'}
        icon = icons.get(obj.notification_method, '?')
        return format_html('{} {}', icon, obj.get_notification_method_display())
    notification_method_display.short_description = 'Méthode'
    notification_method_display.admin_order_field = 'notification_method'

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

    @admin.action(description="✓ Activer les alertes sélectionnées")
    def activate_alerts(self, request, queryset):
        updated = queryset.update(is_active=True)
        messages.success(request, f"{updated} alerte(s) activée(s)")

    @admin.action(description="✗ Désactiver les alertes sélectionnées")
    def deactivate_alerts(self, request, queryset):
        updated = queryset.update(is_active=False)
        messages.success(request, f"{updated} alerte(s) désactivée(s)")


class BlockedSiteCategoryFilter(SimpleListFilter):
    """Filtre par catégorie de site bloqué"""
    title = 'Catégorie'
    parameter_name = 'category'

    def lookups(self, request, model_admin):
        return [
            ('social', '📱 Réseaux sociaux'),
            ('streaming', '🎬 Streaming vidéo'),
            ('gaming', '🎮 Jeux en ligne'),
            ('adult', '🔞 Contenu adulte'),
            ('gambling', '🎰 Jeux d\'argent'),
            ('malware', '🦠 Malware/Phishing'),
            ('ads', '📢 Publicités'),
            ('other', '📋 Autre'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(category=self.value())
        return queryset


@admin.register(BlockedSite)
class BlockedSiteAdmin(DateFormatterMixin, ExportCsvMixin, admin.ModelAdmin):
    """
    Interface d'administration pour les sites bloqués.

    Fonctionnalités:
    - Synchronisation automatique avec MikroTik lors de l'ajout/modification/suppression
    - Actions en masse pour synchroniser ou resynchroniser les entrées
    - Affichage du statut de synchronisation avec indicateurs visuels
    - Filtres par catégorie, statut de sync, et type
    """

    list_per_page = ADMIN_LIST_PER_PAGE
    list_max_show_all = 200

    list_display = [
        'domain', 'category_display', 'type', 'is_active',
        'sync_status_display', 'scope_display', 'added_date_display'
    ]
    list_filter = [
        'is_active', 'type', BlockedSiteCategoryFilter, SyncStatusFilter,
        AddedDateRangeFilter, 'profile', 'promotion'
    ]
    search_fields = ['domain', 'reason', 'profile__name', 'promotion__name', 'added_by__username']
    readonly_fields = [
        'mikrotik_id', 'sync_status', 'last_sync_at',
        'last_sync_error', 'added_date', 'updated_at'
    ]
    autocomplete_fields = ['added_by', 'profile', 'promotion']
    ordering = ['-added_date']
    date_hierarchy = 'added_date'

    # Fix N+1 queries
    list_select_related = ['profile', 'promotion', 'added_by']

    # Actions groupées logiquement (#12):
    # 1. Activation/Désactivation
    # 2. Synchronisation MikroTik
    # 3. Export
    actions = [
        'activate_selected', 'deactivate_selected',  # Groupe 1: État
        'sync_to_mikrotik', 'force_resync',          # Groupe 2: Sync
        'export_as_csv'                               # Groupe 3: Export
    ]

    def get_export_fields(self):
        return ['domain', 'category', 'type', 'is_active', 'sync_status', 'added_date']

    def category_display(self, obj):
        icons = {
            'social': '📱', 'streaming': '🎬', 'gaming': '🎮',
            'adult': '🔞', 'gambling': '🎰', 'malware': '🦠',
            'ads': '📢', 'other': '📋'
        }
        icon = icons.get(obj.category, '📋')
        return format_html('{} {}', icon, obj.get_category_display())
    category_display.short_description = 'Catégorie'
    category_display.admin_order_field = 'category'

    def added_date_display(self, obj):
        return self.format_datetime(obj.added_date)
    added_date_display.short_description = 'Ajouté le'
    added_date_display.admin_order_field = 'added_date'

    fieldsets = (
        ('Domaine à bloquer', {
            'fields': ('domain', 'category', 'type', 'is_active'),
            'description': (
                'Entrez le domaine complet (ex: facebook.com). '
                'Utilisez le préfixe * pour bloquer les sous-domaines (ex: *.tiktok.com)'
            )
        }),
        ('Ciblage (optionnel)', {
            'fields': ('profile', 'promotion'),
            'description': (
                'Laissez vide pour un blocage global. '
                'Sélectionnez un profil OU une promotion pour un blocage ciblé.'
            ),
            'classes': ('collapse',)
        }),
        ('Informations', {
            'fields': ('reason', 'added_by')
        }),
        ('Synchronisation MikroTik', {
            'fields': (
                'mikrotik_id', 'sync_status',
                'last_sync_at', 'last_sync_error'
            ),
            'classes': ('collapse',),
            'description': 'Informations de synchronisation avec le routeur MikroTik'
        }),
        ('Métadonnées', {
            'fields': ('added_date', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def sync_status_display(self, obj):
        """Affiche le statut de sync avec un indicateur visuel"""
        colors = {
            'synced': '#28a745',    # Vert
            'pending': '#ffc107',   # Jaune
            'error': '#dc3545',     # Rouge
        }
        icons = {
            'synced': '✓',
            'pending': '⏳',
            'error': '✗',
        }
        color = colors.get(obj.sync_status, '#6c757d')
        icon = icons.get(obj.sync_status, '?')

        if obj.sync_status == 'error' and obj.last_sync_error:
            title = f"Erreur: {obj.last_sync_error[:100]}"
        elif obj.sync_status == 'synced' and obj.last_sync_at:
            title = f"Synchronisé le {obj.last_sync_at.strftime('%d/%m/%Y %H:%M')}"
        else:
            title = obj.get_sync_status_display()

        return format_html(
            '<span style="color: {}; font-weight: bold;" title="{}">{} {}</span>',
            color, title, icon, obj.get_sync_status_display()
        )
    sync_status_display.short_description = 'Sync MikroTik'
    sync_status_display.admin_order_field = 'sync_status'

    def scope_display(self, obj):
        """Affiche la portée du blocage (global, profil, ou promotion)"""
        if obj.is_global:
            return format_html(
                '<span style="color: #17a2b8;">🌐 Global</span>'
            )
        elif obj.profile:
            return format_html(
                '<span style="color: #6f42c1;">👤 {}</span>',
                obj.profile.name
            )
        elif obj.promotion:
            return format_html(
                '<span style="color: #fd7e14;">🎓 {}</span>',
                obj.promotion.name
            )
        return '-'
    scope_display.short_description = 'Portée'

    def save_model(self, request, obj, form, change):
        """
        Sauvegarde le modèle et synchronise avec MikroTik.

        La synchronisation est effectuée automatiquement après la sauvegarde.
        En cas d'erreur MikroTik, l'entrée est quand même sauvegardée avec
        le statut 'error' pour permettre une resynchronisation ultérieure.

        Utilise une transaction atomique pour éviter les race conditions.
        """
        # Définir l'utilisateur qui ajoute si c'est une création
        if not change:
            obj.added_by = request.user

        # Utiliser une transaction atomique pour éviter les race conditions
        with transaction.atomic():
            # Marquer comme pending si le domaine ou is_active a changé
            if change:
                # Verrouiller la ligne pour éviter les modifications concurrentes
                try:
                    old_obj = BlockedSite.objects.select_for_update(nowait=False).get(pk=obj.pk)
                    if old_obj.domain != obj.domain or old_obj.is_active != obj.is_active:
                        obj.sync_status = 'pending'
                        obj.mikrotik_id = None
                except BlockedSite.DoesNotExist:
                    # L'objet a été supprimé entre-temps
                    messages.error(request, "L'entrée a été supprimée par un autre utilisateur.")
                    return

            # Sauvegarder d'abord
            super().save_model(request, obj, form, change)

        # Tenter la synchronisation avec MikroTik (hors transaction pour ne pas bloquer)
        self._sync_single_site(request, obj)

    def delete_model(self, request, obj):
        """
        Supprime l'entrée DNS de MikroTik avant de supprimer l'objet Django.
        """
        if obj.mikrotik_id:
            try:
                from mikrotik.dns_service import MikrotikDNSBlockingService
                service = MikrotikDNSBlockingService()
                result = service.remove_blocked_domain(obj)
                if result.get('success'):
                    messages.success(
                        request,
                        f"Entrée DNS '{obj.domain}' supprimée de MikroTik"
                    )
                else:
                    messages.warning(
                        request,
                        f"Erreur lors de la suppression sur MikroTik: {result.get('error')}"
                    )
            except Exception as e:
                messages.error(
                    request,
                    f"Impossible de contacter MikroTik: {e}"
                )

        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        """
        Supprime les entrées DNS de MikroTik avant la suppression en masse.
        """
        try:
            from mikrotik.dns_service import MikrotikDNSBlockingService
            service = MikrotikDNSBlockingService()

            removed = 0
            errors = []

            for obj in queryset.filter(mikrotik_id__isnull=False):
                result = service.remove_blocked_domain(obj)
                if result.get('success'):
                    removed += 1
                else:
                    errors.append(f"{obj.domain}: {result.get('error')}")

            if removed > 0:
                messages.success(
                    request,
                    f"{removed} entrée(s) DNS supprimée(s) de MikroTik"
                )
            if errors:
                messages.warning(
                    request,
                    f"Erreurs: {', '.join(errors[:3])}"
                )

        except Exception as e:
            messages.error(
                request,
                f"Impossible de contacter MikroTik: {e}"
            )

        super().delete_queryset(request, queryset)

    def _sync_single_site(self, request, obj):
        """Synchronise un site unique avec MikroTik"""
        try:
            from mikrotik.dns_service import MikrotikDNSBlockingService
            service = MikrotikDNSBlockingService()

            if obj.is_active:
                result = service.update_blocked_domain(obj)
            else:
                result = service.remove_blocked_domain(obj)

            if result.get('success'):
                messages.success(
                    request,
                    f"Site '{obj.domain}' synchronisé avec MikroTik"
                )
            else:
                messages.warning(
                    request,
                    f"Erreur de synchronisation: {result.get('error')}"
                )

        except Exception as e:
            obj.mark_error(str(e))
            messages.error(
                request,
                f"Impossible de contacter MikroTik: {e}. "
                f"L'entrée a été sauvegardée et pourra être synchronisée plus tard."
            )

    @admin.action(description="🔄 Synchroniser avec MikroTik")
    def sync_to_mikrotik(self, request, queryset):
        """
        Action admin pour synchroniser les entrées sélectionnées avec MikroTik.
        """
        try:
            from mikrotik.dns_service import MikrotikDNSBlockingService
            service = MikrotikDNSBlockingService()

            added = 0
            updated = 0
            removed = 0
            errors = []

            for obj in queryset:
                if obj.is_active:
                    if obj.mikrotik_id:
                        result = service.update_blocked_domain(obj)
                        if result.get('success'):
                            updated += 1
                    else:
                        result = service.add_blocked_domain(obj)
                        if result.get('success'):
                            added += 1
                else:
                    result = service.remove_blocked_domain(obj)
                    if result.get('success'):
                        removed += 1

                if not result.get('success'):
                    errors.append(f"{obj.domain}: {result.get('error')}")

            # Messages de résultat
            if added or updated or removed:
                messages.success(
                    request,
                    f"Synchronisation: {added} ajouté(s), "
                    f"{updated} mis à jour, {removed} supprimé(s)"
                )
            if errors:
                messages.warning(
                    request,
                    f"Erreurs ({len(errors)}): {', '.join(errors[:3])}"
                )

        except Exception as e:
            messages.error(request, f"Erreur de connexion MikroTik: {e}")

    @admin.action(description="🔃 Forcer la resynchronisation (⚠️ supprime et recrée)")
    def force_resync(self, request, queryset):
        """
        Force la resynchronisation en supprimant et recréant les entrées.

        Cette action est destructive: elle supprime d'abord l'entrée sur MikroTik
        puis la recrée. Utile en cas de désynchronisation.
        """
        count = queryset.count()

        # Protection: avertir si trop d'éléments sélectionnés
        if count > 50:
            messages.warning(
                request,
                f"⚠️ {count} sites sélectionnés. Pour éviter les surcharges, "
                f"veuillez sélectionner moins de 50 sites à la fois."
            )
            return

        try:
            from mikrotik.dns_service import MikrotikDNSBlockingService
            service = MikrotikDNSBlockingService()

            resynced = 0
            errors = []

            for obj in queryset.filter(is_active=True):
                # Supprimer l'ancienne entrée si elle existe
                if obj.mikrotik_id:
                    service.remove_blocked_domain(obj)

                # Marquer comme pending et recréer
                obj.mark_pending()
                result = service.add_blocked_domain(obj)

                if result.get('success'):
                    resynced += 1
                else:
                    errors.append(f"{obj.domain}: {result.get('error')}")

            if resynced > 0:
                messages.success(
                    request,
                    f"{resynced} site(s) resynchronisé(s)"
                )
            if errors:
                messages.warning(
                    request,
                    f"Erreurs ({len(errors)}): {', '.join(errors[:3])}"
                )

        except Exception as e:
            messages.error(request, f"Erreur de connexion MikroTik: {e}")

    @admin.action(description="✓ Activer les sites sélectionnés")
    def activate_selected(self, request, queryset):
        """Active les sites et les synchronise avec MikroTik"""
        updated = queryset.update(is_active=True, sync_status='pending')
        messages.info(
            request,
            f"{updated} site(s) activé(s). "
            f"Utilisez 'Synchroniser avec MikroTik' pour appliquer."
        )

    @admin.action(description="✗ Désactiver les sites sélectionnés")
    def deactivate_selected(self, request, queryset):
        """Désactive les sites et les supprime de MikroTik"""
        try:
            from mikrotik.dns_service import MikrotikDNSBlockingService
            service = MikrotikDNSBlockingService()

            removed = 0
            for obj in queryset.filter(mikrotik_id__isnull=False):
                result = service.remove_blocked_domain(obj)
                if result.get('success'):
                    removed += 1

            updated = queryset.update(is_active=False)
            messages.success(
                request,
                f"{updated} site(s) désactivé(s), {removed} retiré(s) de MikroTik"
            )

        except Exception as e:
            queryset.update(is_active=False)
            messages.warning(
                request,
                f"Sites désactivés mais erreur MikroTik: {e}"
            )

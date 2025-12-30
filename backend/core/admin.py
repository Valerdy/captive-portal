from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import messages
from django.db import transaction
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    User, Device, Session, Voucher, Promotion, Profile,
    UserProfileUsage, ProfileHistory, ProfileAlert, BlockedSite
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model with RADIUS management actions"""
    list_display = [
        'username', 'email', 'first_name', 'last_name',
        'promotion', 'profile', 'radius_status_display',
        'phone_number', 'is_active'
    ]
    list_filter = [
        'is_active', 'is_staff', 'is_voucher_user', 'is_radius_activated',
        'is_radius_enabled', 'date_joined', 'promotion', 'profile'
    ]
    search_fields = [
        'username', 'email', 'first_name', 'last_name',
        'phone_number', 'mac_address', 'matricule',
        'promotion__name', 'profile__name'
    ]
    ordering = ['-date_joined']
    autocomplete_fields = ['promotion', 'profile']

    # Fix N+1 queries: prefetch FK relations for list view
    list_select_related = ['promotion', 'profile']

    # Actions RADIUS pour gestion en masse
    actions = [
        'activate_radius', 'deactivate_radius',
        'resync_radius', 'enable_radius', 'disable_radius'
    ]

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


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ['name', 'profile', 'is_active', 'user_count_display', 'created_at', 'updated_at']
    list_filter = ['is_active', 'profile']
    search_fields = ['name', 'description', 'profile__name']  # Fix #11: amélioration recherche
    ordering = ['name']
    autocomplete_fields = ['profile']
    list_select_related = ['profile']

    def user_count_display(self, obj):
        """Affiche le nombre d'utilisateurs dans la promotion"""
        count = obj.users.count()
        return format_html('<span title="{} utilisateur(s)">{}</span>', count, count)
    user_count_display.short_description = 'Utilisateurs'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Admin interface for Profile model with RADIUS synchronization actions"""
    list_display = [
        'name', 'quota_type', 'data_volume_display',
        'bandwidth_display', 'validity_duration', 'is_active',
        'radius_status_display', 'created_at'
    ]
    list_filter = [
        'is_active', 'is_radius_enabled', 'quota_type',
        'validity_duration', 'created_at'
    ]
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = [
        'created_at', 'updated_at',
        'data_volume_gb', 'bandwidth_upload_mbps', 'bandwidth_download_mbps',
        'daily_limit_gb', 'weekly_limit_gb', 'monthly_limit_gb',
        'radius_group_name', 'last_radius_sync', 'radius_sync_status'
    ]

    # Actions RADIUS pour gestion en masse
    actions = [
        'enable_radius_sync', 'disable_radius_sync',
        'force_sync_to_radius', 'remove_from_radius'
    ]

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

    # Fix N+1 queries
    list_select_related = ['user']


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

    # Fix N+1 queries
    list_select_related = ['user', 'device']

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


@admin.register(UserProfileUsage)
class UserProfileUsageAdmin(admin.ModelAdmin):
    """Admin interface for UserProfileUsage model"""
    list_display = [
        'user', 'effective_profile_display', 'total_usage_gb_display',
        'daily_usage_display', 'is_exceeded', 'is_expired_display', 'is_active'
    ]
    list_filter = ['is_active', 'is_exceeded', 'activation_date']
    search_fields = ['user__username', 'user__email']
    readonly_fields = [
        'used_today_gb', 'used_week_gb', 'used_month_gb', 'used_total_gb',
        'daily_usage_percent', 'weekly_usage_percent',
        'monthly_usage_percent', 'total_usage_percent',
        'last_daily_reset', 'last_weekly_reset', 'last_monthly_reset',
        'created_at', 'updated_at'
    ]
    autocomplete_fields = ['user']
    ordering = ['-created_at']

    fieldsets = (
        ('Utilisateur', {
            'fields': ('user', 'is_active', 'activation_date')
        }),
        ('Consommation (octets)', {
            'fields': ('used_today', 'used_week', 'used_month', 'used_total')
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

    def effective_profile_display(self, obj):
        """Affiche le profil effectif"""
        profile = obj.get_effective_profile()
        return profile.name if profile else "Aucun"
    effective_profile_display.short_description = 'Profil effectif'

    def total_usage_gb_display(self, obj):
        """Affiche la consommation totale en Go"""
        return f"{obj.used_total_gb} Go"
    total_usage_gb_display.short_description = 'Total consommé'

    def daily_usage_display(self, obj):
        """Affiche la consommation journalière avec pourcentage"""
        return f"{obj.used_today_gb} Go ({round(obj.daily_usage_percent, 1)}%)"
    daily_usage_display.short_description = 'Aujourd\'hui'

    def is_expired_display(self, obj):
        """Affiche si le profil est expiré"""
        return obj.is_expired()
    is_expired_display.boolean = True
    is_expired_display.short_description = 'Expiré'


@admin.register(ProfileHistory)
class ProfileHistoryAdmin(admin.ModelAdmin):
    """Admin interface for ProfileHistory model"""
    list_display = [
        'user', 'change_type', 'old_profile', 'new_profile',
        'changed_by', 'changed_at'
    ]
    list_filter = ['change_type', 'changed_at']
    search_fields = [
        'user__username', 'old_profile__name',
        'new_profile__name', 'changed_by__username'
    ]
    readonly_fields = ['changed_at']
    autocomplete_fields = ['user', 'old_profile', 'new_profile', 'changed_by']
    ordering = ['-changed_at']

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


@admin.register(ProfileAlert)
class ProfileAlertAdmin(admin.ModelAdmin):
    """Admin interface for ProfileAlert model"""
    list_display = [
        'profile', 'alert_type', 'threshold_percent',
        'threshold_days', 'notification_method', 'is_active'
    ]
    list_filter = ['alert_type', 'notification_method', 'is_active', 'created_at']
    search_fields = ['profile__name', 'message_template']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['profile', 'created_by']
    ordering = ['-created_at']

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


@admin.register(BlockedSite)
class BlockedSiteAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour les sites bloqués.

    Fonctionnalités:
    - Synchronisation automatique avec MikroTik lors de l'ajout/modification/suppression
    - Actions en masse pour synchroniser ou resynchroniser les entrées
    - Affichage du statut de synchronisation avec indicateurs visuels
    - Filtres par catégorie, statut de sync, et type
    """

    list_display = [
        'domain', 'category', 'type', 'is_active',
        'sync_status_display', 'scope_display', 'added_date'
    ]
    list_filter = [
        'is_active', 'type', 'category', 'sync_status',
        'added_date', 'profile', 'promotion'
    ]
    search_fields = ['domain', 'reason', 'profile__name', 'promotion__name']
    readonly_fields = [
        'mikrotik_id', 'sync_status', 'last_sync_at',
        'last_sync_error', 'added_date', 'updated_at'
    ]
    autocomplete_fields = ['added_by', 'profile', 'promotion']
    ordering = ['-added_date']

    # Fix N+1 queries
    list_select_related = ['profile', 'promotion', 'added_by']

    # Actions groupées logiquement (#12):
    # 1. Activation/Désactivation
    # 2. Synchronisation MikroTik
    actions = [
        'activate_selected', 'deactivate_selected',  # Groupe 1: État
        'sync_to_mikrotik', 'force_resync',          # Groupe 2: Sync
    ]

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

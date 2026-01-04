from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta


class Profile(models.Model):
    """
    Profil d'abonnement définissant les paramètres RADIUS (bande passante, quota, durée).
    Peut être assigné à des utilisateurs individuels ou à des promotions entières.
    """
    QUOTA_TYPE_CHOICES = [
        ('unlimited', 'Illimité'),
        ('limited', 'Limité'),
    ]

    DURATION_CHOICES = [
        (7, '7 jours'),
        (14, '14 jours'),
        (30, '30 jours'),
        (60, '60 jours'),
        (90, '90 jours'),
        (180, '180 jours'),
        (365, '365 jours'),
    ]

    # Informations de base
    name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Nom du profil (ex: Étudiant, Personnel, Invité)"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Description du profil"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Si désactivé, le profil ne peut pas être assigné"
    )

    # Synchronisation RADIUS
    is_radius_enabled = models.BooleanField(
        default=False,
        help_text="Si activé, le profil est synchronisé vers FreeRADIUS (radgroupreply)"
    )
    radius_group_name = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="Nom du groupe RADIUS (généré automatiquement)"
    )
    last_radius_sync = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date de la dernière synchronisation vers RADIUS"
    )

    # Bande passante (en Mbps) - min 1 Mbps, max 1000 Mbps (1 Gbps)
    bandwidth_upload = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(1000)],
        help_text="Bande passante upload en Mbps (1-1000 Mbps)"
    )
    bandwidth_download = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(1000)],
        help_text="Bande passante download en Mbps (1-1000 Mbps)"
    )

    # Quota de données
    quota_type = models.CharField(
        max_length=20,
        choices=QUOTA_TYPE_CHOICES,
        default='limited',
        help_text="Type de quota (illimité ou limité)"
    )
    data_volume = models.BigIntegerField(
        default=53687091200,  # 50 Go en octets
        help_text="Volume de données attribué en octets (ex: 53687091200 = 50 Go)"
    )

    # Durée de validité
    validity_duration = models.IntegerField(
        choices=DURATION_CHOICES,
        default=30,
        help_text="Durée de validité du quota en jours"
    )

    # Limites périodiques (optionnelles pour le suivi de consommation)
    daily_limit = models.BigIntegerField(
        default=5368709120,  # 5 Go
        null=True,
        blank=True,
        help_text='Limite journalière en octets (ex: 5368709120 = 5 Go)'
    )
    weekly_limit = models.BigIntegerField(
        default=32212254720,  # 30 Go
        null=True,
        blank=True,
        help_text='Limite hebdomadaire en octets (ex: 32212254720 = 30 Go)'
    )
    monthly_limit = models.BigIntegerField(
        default=128849018880,  # 120 Go
        null=True,
        blank=True,
        help_text='Limite mensuelle en octets (ex: 128849018880 = 120 Go)'
    )

    # Paramètres RADIUS supplémentaires
    session_timeout = models.IntegerField(
        default=28800,  # 8 heures en secondes
        help_text="Durée maximale d'une session en secondes (défaut: 8h)"
    )
    idle_timeout = models.IntegerField(
        default=600,  # 10 minutes
        help_text="Délai d'inactivité avant déconnexion en secondes (défaut: 10min)"
    )
    simultaneous_use = models.IntegerField(
        default=1,
        help_text="Nombre de connexions simultanées autorisées"
    )

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profiles_created',
        help_text="Administrateur ayant créé ce profil"
    )

    class Meta:
        db_table = 'profiles'
        ordering = ['name']
        verbose_name = 'Profil'
        verbose_name_plural = 'Profils'

    def __str__(self):
        return f"{self.name} ({self.get_quota_type_display()})"

    @property
    def data_volume_gb(self):
        """Retourne le volume de données en Go"""
        return round(self.data_volume / (1024**3), 2)

    @property
    def bandwidth_upload_mbps(self):
        """Retourne la bande passante upload en Mbps"""
        return self.bandwidth_upload

    @property
    def bandwidth_download_mbps(self):
        """Retourne la bande passante download en Mbps"""
        return self.bandwidth_download

    @property
    def daily_limit_gb(self):
        """Retourne la limite journalière en Go"""
        if self.daily_limit is None:
            return None
        return round(self.daily_limit / (1024**3), 2)

    @property
    def weekly_limit_gb(self):
        """Retourne la limite hebdomadaire en Go"""
        if self.weekly_limit is None:
            return None
        return round(self.weekly_limit / (1024**3), 2)

    @property
    def monthly_limit_gb(self):
        """Retourne la limite mensuelle en Go"""
        if self.monthly_limit is None:
            return None
        return round(self.monthly_limit / (1024**3), 2)

    # =========================================================================
    # Méthodes RADIUS
    # =========================================================================

    def get_radius_group_name(self) -> str:
        """
        Génère le nom du groupe RADIUS pour ce profil.
        Format: profile_{id}_{normalized_name}
        """
        import unicodedata
        import re

        normalized = unicodedata.normalize('NFKD', self.name)
        normalized = normalized.encode('ASCII', 'ignore').decode('ASCII')
        normalized = re.sub(r'[^\w\s-]', '', normalized)
        normalized = re.sub(r'[-\s]+', '_', normalized).lower().strip('_')

        return f"profile_{self.id}_{normalized}"

    def can_sync_to_radius(self) -> bool:
        """Vérifie si le profil peut être synchronisé vers RADIUS."""
        return self.is_active and self.is_radius_enabled

    def sync_to_radius(self) -> dict:
        """
        Synchronise ce profil vers FreeRADIUS.
        Retourne le résultat de la synchronisation.
        """
        from radius.services import RadiusProfileGroupService
        from django.utils import timezone

        if not self.can_sync_to_radius():
            return {
                'success': False,
                'error': 'Profil inactif ou RADIUS désactivé'
            }

        result = RadiusProfileGroupService.sync_profile_to_radius_group(self)

        if result.get('success'):
            # Mettre à jour les métadonnées
            self.radius_group_name = result.get('groupname')
            self.last_radius_sync = timezone.now()
            self.save(update_fields=['radius_group_name', 'last_radius_sync'])

        return result

    def remove_from_radius(self) -> dict:
        """
        Supprime ce profil de FreeRADIUS.
        """
        from radius.services import RadiusProfileGroupService

        result = RadiusProfileGroupService.remove_profile_from_radius_group(self)

        if result.get('success'):
            self.radius_group_name = None
            self.last_radius_sync = None
            self.save(update_fields=['radius_group_name', 'last_radius_sync'])

        return result

    @property
    def is_synced_to_radius(self) -> bool:
        """Vérifie si le profil est actuellement synchronisé dans RADIUS."""
        return bool(self.radius_group_name and self.last_radius_sync)

    @property
    def radius_sync_status(self) -> str:
        """Retourne le statut de synchronisation RADIUS lisible."""
        if not self.is_active:
            return "Profil désactivé"
        if not self.is_radius_enabled:
            return "Sync RADIUS désactivée"
        if self.is_synced_to_radius:
            return f"Synchronisé ({self.radius_group_name})"
        return "En attente de synchronisation"


class Promotion(models.Model):
    """
    Promotion d'étudiants.
    Permet d'activer/désactiver en masse l'accès des utilisateurs à FreeRADIUS.
    """
    name = models.CharField(max_length=100, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)

    # Profil assigné à la promotion
    profile = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='promotions',
        help_text="Profil RADIUS appliqué à tous les utilisateurs de cette promotion"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'promotions'
        ordering = ['name']

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Extended User model for captive portal users"""
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('user', 'User'),
    ]

    # Nouveaux champs pour le système d'inscription
    promotion = models.ForeignKey(
        Promotion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text="Promotion de l'étudiant"
    )
    matricule = models.CharField(max_length=50, blank=True, null=True, help_text="Matricule de l'étudiant")

    # Profil RADIUS individuel (prioritaire sur le profil de la promotion)
    profile = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text="Profil RADIUS individuel (si non défini, utilise le profil de la promotion)"
    )

    # ==========================================================================
    # RADIUS Status Management (Fix #24: Documentation clarifiée)
    # ==========================================================================
    # Deux états DISTINCTS pour gérer le cycle de vie RADIUS:
    #
    # 1. is_radius_activated (alias: "Provisionné dans RADIUS")
    #    - PERMANENT: Indique si l'utilisateur a été créé dans les tables RADIUS
    #    - False → Jamais créé dans radcheck/radreply/radusergroup
    #    - True  → Utilisateur créé dans les tables RADIUS (action irréversible)
    #    - Ne peut passer de True à False que par suppression complète
    #
    # 2. is_radius_enabled (alias: "Accès WiFi actif")
    #    - TEMPORAIRE: Contrôle si l'accès WiFi est actuellement autorisé
    #    - True  → Peut se connecter au WiFi (statut=1 dans radcheck)
    #    - False → NE peut PAS se connecter (statut=0 dans radcheck)
    #    - Toggle on/off par admin à volonté
    #
    # Combinaisons possibles:
    # - activated=False, enabled=True  → En attente d'activation (inscription)
    # - activated=True,  enabled=True  → Accès WiFi actif ✓
    # - activated=True,  enabled=False → Accès WiFi suspendu (quota, admin, etc.)
    # - activated=False, enabled=False → Jamais activé, accès désactivé
    # ==========================================================================
    is_radius_activated = models.BooleanField(
        default=False,
        verbose_name="Provisionné RADIUS",
        help_text=(
            "PERMANENT: Indique si l'utilisateur a été créé dans RADIUS "
            "(radcheck/radreply/radusergroup). Passe à True lors de la première activation."
        )
    )
    is_radius_enabled = models.BooleanField(
        default=True,
        verbose_name="Accès WiFi actif",
        help_text=(
            "TEMPORAIRE: Contrôle si l'utilisateur peut accéder au WiFi. "
            "Toggle on/off par admin. Modifie statut dans radcheck."
        )
    )

    # ATTENTION SÉCURITÉ: Mot de passe en clair pour RADIUS
    # Ce champ stocke le mot de passe en clair pour pouvoir le copier dans radcheck lors de l'activation
    # RISQUE: Si la base de données est compromise, les mots de passe sont exposés
    cleartext_password = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text="Mot de passe en clair (UNIQUEMENT pour activation RADIUS - RISQUE DE SÉCURITÉ)"
    )

    # Champs existants
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    mac_address = models.CharField(max_length=17, blank=True, null=True, db_index=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    is_voucher_user = models.BooleanField(default=False)
    voucher_code = models.CharField(max_length=50, blank=True, null=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='user', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_radius_activated', 'is_radius_enabled']),
            models.Index(fields=['promotion', 'is_active']),
            models.Index(fields=['is_active', 'is_radius_activated']),
            models.Index(fields=['profile', 'is_active']),
            models.Index(fields=['date_joined']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.username} ({self.email})"

    def get_role_name(self):
        """Get the role name (synced with is_staff/is_superuser)"""
        if self.is_staff or self.is_superuser:
            return 'admin'
        return 'user'

    def is_admin(self):
        """Check if user has admin role"""
        return self.is_staff or self.is_superuser or self.role == 'admin'

    def is_regular_user(self):
        """Check if user has regular user role"""
        return not self.is_admin()

    # RADIUS Helper Methods
    def can_access_radius(self):
        """
        Vérifie si l'utilisateur peut accéder au WiFi via RADIUS.
        Retourne True SEULEMENT si:
        - L'utilisateur est activé dans Django (is_active=True)
        - L'utilisateur a été provisionné dans RADIUS (is_radius_activated=True)
        - L'accès RADIUS est actuellement activé (is_radius_enabled=True)
        """
        return self.is_active and self.is_radius_activated and self.is_radius_enabled

    def is_pending_radius_activation(self):
        """
        Vérifie si l'utilisateur est en attente d'activation RADIUS.
        Retourne True si l'utilisateur est actif mais pas encore provisionné dans RADIUS.
        """
        return self.is_active and not self.is_radius_activated

    def get_radius_status_display(self):
        """
        Retourne un statut RADIUS lisible pour les humains.
        """
        if not self.is_active:
            return "Compte Django désactivé"
        if not self.is_radius_activated:
            return "En attente d'activation RADIUS"
        if not self.is_radius_enabled:
            return "Accès WiFi désactivé"
        return "Accès WiFi actif"

    def get_effective_profile(self):
        """
        Retourne le profil RADIUS effectif pour cet utilisateur.
        Priorité: profil individuel > profil de la promotion > None
        """
        if self.profile:
            return self.profile
        if self.promotion and self.promotion.profile:
            return self.promotion.profile
        return None


class Device(models.Model):
    """Device information for connected clients"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    mac_address = models.CharField(max_length=17, unique=True, db_index=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    hostname = models.CharField(max_length=255, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    device_type = models.CharField(max_length=50, blank=True, null=True)  # mobile, desktop, tablet
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'devices'
        ordering = ['-last_seen']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['last_seen']),
        ]

    def __str__(self):
        return f"{self.mac_address} - {self.user.username}"


class Session(models.Model):
    """User session tracking"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='sessions')
    session_id = models.CharField(max_length=255, unique=True, db_index=True)
    ip_address = models.GenericIPAddressField()
    mac_address = models.CharField(max_length=17, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # Session timing
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    timeout_duration = models.IntegerField(default=3600)  # seconds

    # Data usage
    bytes_in = models.BigIntegerField(default=0)
    bytes_out = models.BigIntegerField(default=0)
    packets_in = models.BigIntegerField(default=0)
    packets_out = models.BigIntegerField(default=0)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sessions'
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['status', 'start_time']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"Session {self.session_id} - {self.user.username}"

    @property
    def is_expired(self):
        """Check if session has expired"""
        if self.status != 'active':
            return True
        if self.end_time and timezone.now() > self.end_time:
            return True
        timeout = self.start_time + timedelta(seconds=self.timeout_duration)
        return timezone.now() > timeout

    @property
    def total_bytes(self):
        """Total data transferred"""
        return self.bytes_in + self.bytes_out


class Voucher(models.Model):
    """Voucher codes for guest access"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('used', 'Used'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
    ]

    code = models.CharField(max_length=50, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    duration = models.IntegerField(help_text='Session duration in seconds')
    max_devices = models.IntegerField(default=1)
    used_count = models.IntegerField(default=0)

    # Validity period
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField()

    # Usage tracking
    used_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='vouchers_used')
    used_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='vouchers_created')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'vouchers'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'valid_until']),
            models.Index(fields=['created_by', 'created_at']),
        ]

    def __str__(self):
        return f"Voucher {self.code} - {self.status}"

    @property
    def is_valid(self):
        """Check if voucher is still valid"""
        now = timezone.now()
        return (
            self.status == 'active' and
            self.valid_from <= now <= self.valid_until and
            self.used_count < self.max_devices
        )


class BlockedSite(models.Model):
    """
    Gestion des sites bloqués via DNS statique MikroTik.

    Le blocage fonctionne en créant une entrée DNS statique sur le routeur MikroTik
    qui redirige le domaine vers 0.0.0.0, rendant le site inaccessible.

    Cette méthode fonctionne pour HTTP et HTTPS car le blocage se fait au niveau DNS.
    """

    TYPE_CHOICES = [
        ('blacklist', 'Blacklist'),
        ('whitelist', 'Whitelist'),
    ]

    SYNC_STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('synced', 'Synchronisé'),
        ('error', 'Erreur'),
    ]

    CATEGORY_CHOICES = [
        ('social', 'Réseaux sociaux'),
        ('streaming', 'Streaming vidéo'),
        ('gaming', 'Jeux en ligne'),
        ('adult', 'Contenu adulte'),
        ('gambling', 'Jeux d\'argent'),
        ('malware', 'Malware/Phishing'),
        ('ads', 'Publicités'),
        ('other', 'Autre'),
    ]

    # Domaine à bloquer (ex: facebook.com, *.tiktok.com)
    domain = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text='Domaine à bloquer (ex: facebook.com). Utilisez le préfixe * pour les sous-domaines (*.example.com)'
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='blacklist')
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='other',
        help_text='Catégorie du site pour le regroupement et les statistiques'
    )
    reason = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Raison du blocage (visible dans les logs)'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Désactiver pour suspendre temporairement le blocage sans supprimer l\'entrée'
    )

    # Extension future: blocage par profil ou promotion
    profile = models.ForeignKey(
        'Profile',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='blocked_sites',
        help_text='Profil concerné (laisser vide pour bloquer globalement)'
    )
    promotion = models.ForeignKey(
        'Promotion',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='blocked_sites',
        help_text='Promotion concernée (laisser vide pour bloquer globalement)'
    )

    # Synchronisation MikroTik
    mikrotik_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='ID de l\'entrée DNS statique sur MikroTik (géré automatiquement)'
    )
    sync_status = models.CharField(
        max_length=20,
        choices=SYNC_STATUS_CHOICES,
        default='pending',
        help_text='État de la synchronisation avec MikroTik'
    )
    last_sync_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Date de la dernière synchronisation réussie'
    )
    last_sync_error = models.TextField(
        blank=True,
        null=True,
        help_text='Dernier message d\'erreur de synchronisation'
    )

    # Metadata
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='blocked_sites'
    )
    added_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'blocked_sites'
        ordering = ['-added_date']
        verbose_name = 'Site bloqué'
        verbose_name_plural = 'Sites bloqués'
        indexes = [
            models.Index(fields=['type', 'is_active']),
            models.Index(fields=['sync_status']),
            models.Index(fields=['category']),
        ]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(profile__isnull=False, promotion__isnull=False),
                name='blocked_site_profile_or_promotion_not_both'
            )
        ]

    def __str__(self):
        status = '✓' if self.sync_status == 'synced' else '⏳' if self.sync_status == 'pending' else '✗'
        return f"{status} {self.domain} ({self.get_category_display()})"

    @property
    def is_global(self) -> bool:
        """Vérifie si le blocage est global (pas de profil ni promotion)"""
        return self.profile is None and self.promotion is None

    @property
    def needs_sync(self) -> bool:
        """Vérifie si une synchronisation est nécessaire"""
        return self.sync_status in ('pending', 'error')

    def get_dns_name(self) -> str:
        """
        Retourne le nom DNS à utiliser pour l'entrée MikroTik.
        Gère les wildcards (*.example.com -> regexp)
        """
        return self.domain.lstrip('*.')

    def mark_synced(self, mikrotik_id: str = None) -> None:
        """Marque l'entrée comme synchronisée"""
        self.sync_status = 'synced'
        self.last_sync_at = timezone.now()
        self.last_sync_error = None
        if mikrotik_id:
            self.mikrotik_id = mikrotik_id
        self.save(update_fields=['sync_status', 'last_sync_at', 'last_sync_error', 'mikrotik_id'])

    def mark_error(self, error_message: str) -> None:
        """Marque l'entrée comme en erreur"""
        self.sync_status = 'error'
        self.last_sync_error = str(error_message)[:1000]  # Limiter la taille
        self.save(update_fields=['sync_status', 'last_sync_error'])

    def mark_pending(self) -> None:
        """Marque l'entrée comme en attente de sync"""
        self.sync_status = 'pending'
        self.mikrotik_id = None
        self.save(update_fields=['sync_status', 'mikrotik_id'])


class UserQuota(models.Model):
    """User bandwidth quota management"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='quota')

    # Quota limits (in bytes)
    daily_limit = models.BigIntegerField(default=5368709120, help_text='Daily limit in bytes (default 5GB)')
    weekly_limit = models.BigIntegerField(default=32212254720, help_text='Weekly limit in bytes (default 30GB)')
    monthly_limit = models.BigIntegerField(default=128849018880, help_text='Monthly limit in bytes (default 120GB)')

    # Current usage (in bytes)
    used_today = models.BigIntegerField(default=0)
    used_week = models.BigIntegerField(default=0)
    used_month = models.BigIntegerField(default=0)

    # Reset timestamps
    last_daily_reset = models.DateTimeField(default=timezone.now)
    last_weekly_reset = models.DateTimeField(default=timezone.now)
    last_monthly_reset = models.DateTimeField(default=timezone.now)

    # Status
    is_active = models.BooleanField(default=True)
    is_exceeded = models.BooleanField(default=False, help_text='True if any quota is exceeded')

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_quotas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_exceeded', 'is_active']),
        ]

    def __str__(self):
        return f"Quota for {self.user.username}"

    def reset_daily(self):
        """Reset daily usage counter"""
        self.used_today = 0
        self.last_daily_reset = timezone.now()
        self.check_exceeded()
        self.save()

    def reset_weekly(self):
        """Reset weekly usage counter"""
        self.used_week = 0
        self.last_weekly_reset = timezone.now()
        self.check_exceeded()
        self.save()

    def reset_monthly(self):
        """Reset monthly usage counter"""
        self.used_month = 0
        self.last_monthly_reset = timezone.now()
        self.check_exceeded()
        self.save()

    def reset_all(self):
        """Reset all usage counters"""
        self.used_today = 0
        self.used_week = 0
        self.used_month = 0
        self.last_daily_reset = timezone.now()
        self.last_weekly_reset = timezone.now()
        self.last_monthly_reset = timezone.now()
        self.is_exceeded = False
        self.save()

    def check_exceeded(self):
        """Check if any quota limit is exceeded"""
        self.is_exceeded = (
            self.used_today >= self.daily_limit or
            self.used_week >= self.weekly_limit or
            self.used_month >= self.monthly_limit
        )
        return self.is_exceeded

    def add_usage(self, bytes_used):
        """Add bandwidth usage to all counters"""
        self.used_today += bytes_used
        self.used_week += bytes_used
        self.used_month += bytes_used
        self.check_exceeded()
        self.save()

    @property
    def daily_usage_percent(self):
        """Calculate daily usage percentage"""
        if self.daily_limit == 0:
            return 0
        return min(100, (self.used_today / self.daily_limit) * 100)

    @property
    def weekly_usage_percent(self):
        """Calculate weekly usage percentage"""
        if self.weekly_limit == 0:
            return 0
        return min(100, (self.used_week / self.weekly_limit) * 100)

    @property
    def monthly_usage_percent(self):
        """Calculate monthly usage percentage"""
        if self.monthly_limit == 0:
            return 0
        return min(100, (self.used_month / self.monthly_limit) * 100)


class UserProfileUsage(models.Model):
    """
    Suivi de consommation utilisateur basé sur le profil assigné.
    Remplace UserQuota avec une architecture plus cohérente.
    """
    user = models.OneToOneField(
        'User',
        on_delete=models.CASCADE,
        related_name='profile_usage',
        help_text="Utilisateur dont on suit la consommation"
    )

    # Consommation en temps réel (en octets)
    used_today = models.BigIntegerField(
        default=0,
        help_text="Consommation aujourd'hui en octets"
    )
    used_week = models.BigIntegerField(
        default=0,
        help_text="Consommation cette semaine en octets"
    )
    used_month = models.BigIntegerField(
        default=0,
        help_text="Consommation ce mois en octets"
    )
    used_total = models.BigIntegerField(
        default=0,
        help_text="Consommation totale depuis l'activation du profil actuel en octets"
    )

    # Dates de reset
    last_daily_reset = models.DateTimeField(
        default=timezone.now,
        help_text="Date du dernier reset journalier"
    )
    last_weekly_reset = models.DateTimeField(
        default=timezone.now,
        help_text="Date du dernier reset hebdomadaire"
    )
    last_monthly_reset = models.DateTimeField(
        default=timezone.now,
        help_text="Date du dernier reset mensuel"
    )
    activation_date = models.DateTimeField(
        default=timezone.now,
        help_text="Date d'activation du profil actuel (pour validity_duration)"
    )

    # Statut
    is_exceeded = models.BooleanField(
        default=False,
        help_text="True si un quota est dépassé"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Active le suivi de consommation"
    )

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profile_usage'
        ordering = ['-created_at']
        verbose_name = 'Utilisation de profil'
        verbose_name_plural = 'Utilisations de profils'
        indexes = [
            models.Index(fields=['is_exceeded', 'is_active']),
            models.Index(fields=['activation_date']),
        ]

    def __str__(self):
        return f"Usage de {self.user.username}"

    def get_effective_profile(self):
        """Récupère le profil effectif de l'utilisateur"""
        return self.user.get_effective_profile()

    def reset_daily(self):
        """Réinitialise le compteur journalier"""
        self.used_today = 0
        self.last_daily_reset = timezone.now()
        self.check_exceeded()
        self.save()

    def reset_weekly(self):
        """Réinitialise le compteur hebdomadaire"""
        self.used_week = 0
        self.last_weekly_reset = timezone.now()
        self.check_exceeded()
        self.save()

    def reset_monthly(self):
        """Réinitialise le compteur mensuel"""
        self.used_month = 0
        self.last_monthly_reset = timezone.now()
        self.check_exceeded()
        self.save()

    def reset_all(self):
        """Réinitialise tous les compteurs"""
        self.used_today = 0
        self.used_week = 0
        self.used_month = 0
        self.used_total = 0
        self.last_daily_reset = timezone.now()
        self.last_weekly_reset = timezone.now()
        self.last_monthly_reset = timezone.now()
        self.activation_date = timezone.now()
        self.is_exceeded = False
        self.save()

    def check_exceeded(self):
        """Vérifie si un quota est dépassé en se basant sur le profil effectif"""
        profile = self.get_effective_profile()
        if not profile:
            self.is_exceeded = False
            return False

        # Vérifier les limites périodiques si définies
        daily_exceeded = (
            profile.daily_limit is not None and
            self.used_today >= profile.daily_limit
        )
        weekly_exceeded = (
            profile.weekly_limit is not None and
            self.used_week >= profile.weekly_limit
        )
        monthly_exceeded = (
            profile.monthly_limit is not None and
            self.used_month >= profile.monthly_limit
        )

        # Vérifier le quota total si limité
        total_exceeded = False
        if profile.quota_type == 'limited':
            total_exceeded = self.used_total >= profile.data_volume

        self.is_exceeded = (
            daily_exceeded or weekly_exceeded or
            monthly_exceeded or total_exceeded
        )
        return self.is_exceeded

    def add_usage(self, bytes_used):
        """Ajoute de la consommation à tous les compteurs"""
        self.used_today += bytes_used
        self.used_week += bytes_used
        self.used_month += bytes_used
        self.used_total += bytes_used
        self.check_exceeded()
        self.save()

    def is_expired(self):
        """Vérifie si le profil est expiré basé sur validity_duration"""
        profile = self.get_effective_profile()
        if not profile:
            return False

        expiry_date = self.activation_date + timedelta(days=profile.validity_duration)
        return timezone.now() > expiry_date

    def days_remaining(self):
        """Retourne le nombre de jours restants avant expiration"""
        profile = self.get_effective_profile()
        if not profile:
            return None

        expiry_date = self.activation_date + timedelta(days=profile.validity_duration)
        remaining = expiry_date - timezone.now()
        return max(0, remaining.days)

    @property
    def daily_usage_percent(self):
        """Calcule le pourcentage d'utilisation journalier"""
        profile = self.get_effective_profile()
        if not profile or profile.daily_limit is None or profile.daily_limit == 0:
            return 0
        return min(100, (self.used_today / profile.daily_limit) * 100)

    @property
    def weekly_usage_percent(self):
        """Calcule le pourcentage d'utilisation hebdomadaire"""
        profile = self.get_effective_profile()
        if not profile or profile.weekly_limit is None or profile.weekly_limit == 0:
            return 0
        return min(100, (self.used_week / profile.weekly_limit) * 100)

    @property
    def monthly_usage_percent(self):
        """Calcule le pourcentage d'utilisation mensuel"""
        profile = self.get_effective_profile()
        if not profile or profile.monthly_limit is None or profile.monthly_limit == 0:
            return 0
        return min(100, (self.used_month / profile.monthly_limit) * 100)

    @property
    def total_usage_percent(self):
        """Calcule le pourcentage d'utilisation total"""
        profile = self.get_effective_profile()
        if not profile or profile.quota_type == 'unlimited':
            return 0
        if profile.data_volume == 0:
            return 0
        return min(100, (self.used_total / profile.data_volume) * 100)

    @property
    def used_today_gb(self):
        """Retourne la consommation journalière en Go"""
        return round(self.used_today / (1024**3), 2)

    @property
    def used_week_gb(self):
        """Retourne la consommation hebdomadaire en Go"""
        return round(self.used_week / (1024**3), 2)

    @property
    def used_month_gb(self):
        """Retourne la consommation mensuelle en Go"""
        return round(self.used_month / (1024**3), 2)

    @property
    def used_total_gb(self):
        """Retourne la consommation totale en Go"""
        return round(self.used_total / (1024**3), 2)


class ProfileHistory(models.Model):
    """
    Historique des changements de profils pour audit trail.
    Permet de tracker qui a changé le profil de qui et quand.
    """
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='profile_history',
        help_text="Utilisateur dont le profil a été modifié"
    )
    old_profile = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='history_as_old',
        help_text="Ancien profil (null si premier profil)"
    )
    new_profile = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='history_as_new',
        help_text="Nouveau profil (null si suppression)"
    )
    changed_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='profile_changes_made',
        help_text="Administrateur qui a effectué le changement"
    )
    changed_at = models.DateTimeField(
        default=timezone.now,
        help_text="Date du changement"
    )
    reason = models.TextField(
        blank=True,
        null=True,
        help_text="Raison du changement (optionnel)"
    )
    change_type = models.CharField(
        max_length=20,
        choices=[
            ('assigned', 'Assignation'),
            ('updated', 'Modification'),
            ('removed', 'Suppression'),
        ],
        default='assigned',
        help_text="Type de changement"
    )

    class Meta:
        db_table = 'profile_history'
        ordering = ['-changed_at']
        verbose_name = 'Historique de profil'
        verbose_name_plural = 'Historiques de profils'
        indexes = [
            models.Index(fields=['user', '-changed_at']),
            models.Index(fields=['changed_by', '-changed_at']),
        ]

    def __str__(self):
        if self.change_type == 'assigned':
            return f"{self.user.username}: Profil assigné à '{self.new_profile.name if self.new_profile else 'None'}'"
        elif self.change_type == 'updated':
            return f"{self.user.username}: '{self.old_profile.name if self.old_profile else 'None'}' → '{self.new_profile.name if self.new_profile else 'None'}'"
        else:
            return f"{self.user.username}: Profil supprimé"


class ProfileAlert(models.Model):
    """
    Système d'alertes automatiques basé sur les seuils de consommation.
    Permet de notifier les utilisateurs et admins quand certains seuils sont atteints.
    """
    ALERT_TYPE_CHOICES = [
        ('quota_warning', 'Avertissement quota'),
        ('quota_critical', 'Quota critique'),
        ('expiry_warning', 'Avertissement expiration'),
        ('expiry_imminent', 'Expiration imminente'),
    ]

    NOTIFICATION_METHOD_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('system', 'Notification système'),
        ('all', 'Tous les canaux'),
    ]

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='alerts',
        help_text="Profil concerné par l'alerte"
    )
    alert_type = models.CharField(
        max_length=20,
        choices=ALERT_TYPE_CHOICES,
        help_text="Type d'alerte"
    )
    threshold_percent = models.IntegerField(
        default=80,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Seuil en pourcentage pour déclencher l'alerte (0-100%)"
    )
    threshold_days = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Nombre de jours avant expiration pour déclencher l'alerte (min: 1 jour)"
    )
    notification_method = models.CharField(
        max_length=20,
        choices=NOTIFICATION_METHOD_CHOICES,
        default='system',
        help_text="Méthode de notification"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Active ou désactive cette alerte"
    )
    message_template = models.TextField(
        blank=True,
        null=True,
        help_text="Template du message (peut contenir {username}, {percent}, {remaining_gb}, etc.)"
    )

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alerts_created',
        help_text="Administrateur ayant créé cette alerte"
    )

    class Meta:
        db_table = 'profile_alerts'
        ordering = ['-created_at']
        verbose_name = 'Alerte de profil'
        verbose_name_plural = 'Alertes de profils'
        unique_together = ['profile', 'alert_type', 'threshold_percent']

    def __str__(self):
        return f"{self.profile.name} - {self.get_alert_type_display()} @ {self.threshold_percent}%"

    def should_trigger(self, usage):
        """Vérifie si l'alerte doit être déclenchée pour un UserProfileUsage donné"""
        if not self.is_active:
            return False

        if self.alert_type in ['quota_warning', 'quota_critical']:
            # Alerte basée sur le pourcentage de consommation
            usage_percent = usage.total_usage_percent
            return usage_percent >= self.threshold_percent

        elif self.alert_type in ['expiry_warning', 'expiry_imminent']:
            # Alerte basée sur les jours restants
            if self.threshold_days is None:
                return False
            days_remaining = usage.days_remaining()
            return days_remaining is not None and days_remaining <= self.threshold_days

        return False


class UserDisconnectionLog(models.Model):
    """
    Logs des déconnexions automatiques d'utilisateurs
    Stocke pourquoi un utilisateur a été désactivé (quota atteint, session expirée, etc.)
    """
    REASON_CHOICES = [
        ('quota_exceeded', 'Quota de données dépassé'),
        ('session_expired', 'Session expirée'),
        ('daily_limit', 'Limite journalière atteinte'),
        ('weekly_limit', 'Limite hebdomadaire atteinte'),
        ('monthly_limit', 'Limite mensuelle atteinte'),
        ('idle_timeout', 'Délai d\'inactivité dépassé'),
        ('validity_expired', 'Durée de validité expirée'),
        ('manual', 'Désactivation manuelle par admin'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='disconnection_logs',
        help_text="Utilisateur concerné"
    )
    reason = models.CharField(
        max_length=50,
        choices=REASON_CHOICES,
        help_text="Raison de la déconnexion"
    )
    description = models.TextField(
        blank=True,
        help_text="Description détaillée de la raison"
    )
    disconnected_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date et heure de la déconnexion"
    )
    reconnected_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date et heure de la reconnexion (si réactivé)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="True si l'utilisateur est toujours déconnecté"
    )
    reconnected_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reconnections_performed',
        help_text="Admin qui a réactivé l'utilisateur"
    )

    # Données au moment de la déconnexion (pour référence)
    quota_used = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Quota utilisé en octets au moment de la déconnexion"
    )
    quota_limit = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Limite de quota en octets"
    )
    session_duration = models.IntegerField(
        null=True,
        blank=True,
        help_text="Durée de la session en secondes"
    )

    class Meta:
        db_table = 'user_disconnection_logs'
        ordering = ['-disconnected_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['disconnected_at']),
            models.Index(fields=['reason']),
        ]
        verbose_name = "Log de déconnexion"
        verbose_name_plural = "Logs de déconnexions"

    def __str__(self):
        status = "Actif" if self.is_active else "Résolu"
        return f"{self.user.username} - {self.get_reason_display()} ({status})"

    def reactivate(self, admin_user=None):
        """Marque la déconnexion comme résolue et réactive l'utilisateur"""
        from django.utils import timezone
        self.is_active = False
        self.reconnected_at = timezone.now()
        if admin_user:
            self.reconnected_by = admin_user
        self.save()


# =============================================================================
# Audit et Suivi de Synchronisation (Fixes #7, #10, #12)
# =============================================================================

class AdminAuditLog(models.Model):
    """
    Journalisation des actions administrateur critiques.
    Fix #10: Traçabilité complète WHO, WHEN, WHAT.
    """
    ACTION_TYPES = [
        # User RADIUS actions
        ('user_radius_activate', 'Activation RADIUS utilisateur'),
        ('user_radius_deactivate', 'Désactivation RADIUS utilisateur'),
        ('user_radius_reactivate', 'Réactivation RADIUS utilisateur'),
        ('user_radius_sync', 'Synchronisation RADIUS utilisateur'),
        # Profile actions
        ('profile_radius_enable', 'Activation RADIUS profil'),
        ('profile_radius_disable', 'Désactivation RADIUS profil'),
        ('profile_radius_sync', 'Synchronisation RADIUS profil'),
        ('profile_create', 'Création profil'),
        ('profile_update', 'Modification profil'),
        ('profile_delete', 'Suppression profil'),
        # Promotion actions
        ('promotion_activate', 'Activation promotion'),
        ('promotion_deactivate', 'Désactivation promotion'),
        # Bulk actions
        ('bulk_radius_enable', 'Activation RADIUS en masse'),
        ('bulk_radius_disable', 'Désactivation RADIUS en masse'),
        ('bulk_user_activate', 'Activation utilisateurs en masse'),
        ('bulk_user_deactivate', 'Désactivation utilisateurs en masse'),
        # Other
        ('voucher_create', 'Création voucher'),
        ('voucher_revoke', 'Révocation voucher'),
        ('blocked_site_add', 'Ajout site bloqué'),
        ('blocked_site_remove', 'Suppression site bloqué'),
    ]

    SEVERITY_LEVELS = [
        ('info', 'Information'),
        ('warning', 'Avertissement'),
        ('critical', 'Critique'),
    ]

    # Qui a fait l'action
    admin_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        help_text="Administrateur ayant effectué l'action"
    )
    admin_username = models.CharField(
        max_length=150,
        help_text="Username de l'admin (conservé si user supprimé)"
    )
    admin_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Adresse IP de l'administrateur"
    )

    # Quoi
    action_type = models.CharField(
        max_length=50,
        choices=ACTION_TYPES,
        db_index=True,
        help_text="Type d'action effectuée"
    )
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_LEVELS,
        default='info',
        help_text="Niveau de sévérité"
    )

    # Sur quoi (polymorphique)
    target_model = models.CharField(
        max_length=50,
        help_text="Modèle cible (User, Profile, Promotion, etc.)"
    )
    target_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID de l'objet cible"
    )
    target_repr = models.CharField(
        max_length=255,
        help_text="Représentation textuelle de la cible"
    )

    # Détails
    details = models.JSONField(
        default=dict,
        help_text="Détails de l'action (paramètres, résultats)"
    )
    success = models.BooleanField(
        default=True,
        help_text="L'action a-t-elle réussi?"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Message d'erreur si échec"
    )

    # Quand
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        db_table = 'admin_audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action_type', 'created_at']),
            models.Index(fields=['admin_user', 'created_at']),
            models.Index(fields=['target_model', 'target_id']),
        ]
        verbose_name = "Log d'audit admin"
        verbose_name_plural = "Logs d'audit admin"

    def __str__(self):
        return f"{self.admin_username} - {self.get_action_type_display()} - {self.target_repr}"

    @classmethod
    def log_action(cls, admin_user, action_type, target, details=None,
                   success=True, error_message=None, request=None, severity='info'):
        """
        Crée une entrée de log d'audit.

        Args:
            admin_user: L'utilisateur admin effectuant l'action
            action_type: Type d'action (doit être dans ACTION_TYPES)
            target: L'objet cible (User, Profile, etc.) ou tuple (model_name, id, repr)
            details: Dict avec les détails supplémentaires
            success: L'action a-t-elle réussi?
            error_message: Message d'erreur si échec
            request: La requête HTTP pour extraire l'IP
            severity: Niveau de sévérité (info, warning, critical)
        """
        # Gérer le cas où target est un tuple
        if isinstance(target, tuple):
            target_model, target_id, target_repr = target
        else:
            target_model = target.__class__.__name__
            target_id = getattr(target, 'pk', None) or getattr(target, 'id', None)
            target_repr = str(target)[:255]

        # Extraire l'IP de la requête
        admin_ip = None
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                admin_ip = x_forwarded_for.split(',')[0].strip()
            else:
                admin_ip = request.META.get('REMOTE_ADDR')

        return cls.objects.create(
            admin_user=admin_user,
            admin_username=admin_user.username if admin_user else 'system',
            admin_ip=admin_ip,
            action_type=action_type,
            severity=severity,
            target_model=target_model,
            target_id=target_id,
            target_repr=target_repr,
            details=details or {},
            success=success,
            error_message=error_message
        )


class SyncFailureLog(models.Model):
    """
    Journal des échecs de synchronisation entre Django, RADIUS et MikroTik.
    Fix #7 et #12: Traçabilité des erreurs de sync pour retry et alertes.
    """
    SYNC_TYPES = [
        ('radius_user', 'Utilisateur → RADIUS'),
        ('radius_profile', 'Profil → RADIUS Group'),
        ('radius_group', 'Utilisateur → RADIUS Group'),
        ('mikrotik_user', 'Utilisateur → MikroTik'),
        ('mikrotik_profile', 'Profil → MikroTik'),
        ('mikrotik_dns', 'Site bloqué → MikroTik DNS'),
    ]

    STATUS_CHOICES = [
        ('pending', 'En attente de retry'),
        ('retrying', 'Retry en cours'),
        ('resolved', 'Résolu'),
        ('failed', 'Échec définitif'),
        ('ignored', 'Ignoré'),
    ]

    # Type de synchronisation
    sync_type = models.CharField(
        max_length=30,
        choices=SYNC_TYPES,
        db_index=True
    )

    # Objet source (polymorphique)
    source_model = models.CharField(max_length=50)
    source_id = models.IntegerField()
    source_repr = models.CharField(max_length=255)

    # Détails de l'erreur
    error_message = models.TextField(
        help_text="Message d'erreur détaillé"
    )
    error_traceback = models.TextField(
        blank=True,
        null=True,
        help_text="Traceback Python complet"
    )

    # Contexte
    context = models.JSONField(
        default=dict,
        help_text="Contexte de l'opération (paramètres, état)"
    )

    # Gestion des retries
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    retry_count = models.IntegerField(
        default=0,
        help_text="Nombre de tentatives de retry"
    )
    max_retries = models.IntegerField(
        default=3,
        help_text="Nombre maximum de retries"
    )
    next_retry_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date/heure du prochain retry"
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date/heure de résolution"
    )
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_sync_failures',
        help_text="Admin ayant résolu l'échec"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sync_failure_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sync_type', 'status']),
            models.Index(fields=['source_model', 'source_id']),
            models.Index(fields=['status', 'next_retry_at']),
        ]
        verbose_name = "Échec de synchronisation"
        verbose_name_plural = "Échecs de synchronisation"

    def __str__(self):
        return f"{self.get_sync_type_display()} - {self.source_repr} ({self.get_status_display()})"

    @classmethod
    def log_failure(cls, sync_type, source, error, context=None, traceback_str=None):
        """
        Enregistre un échec de synchronisation.

        Args:
            sync_type: Type de sync (doit être dans SYNC_TYPES)
            source: L'objet source (User, Profile, etc.)
            error: L'exception ou message d'erreur
            context: Dict avec le contexte de l'opération
            traceback_str: Traceback formaté
        """
        from django.utils import timezone
        from datetime import timedelta

        source_model = source.__class__.__name__
        source_id = getattr(source, 'pk', None) or getattr(source, 'id', None)
        source_repr = str(source)[:255]

        error_message = str(error) if error else 'Unknown error'

        # Calculer le prochain retry (backoff exponentiel: 2min, 8min, 32min)
        next_retry = timezone.now() + timedelta(minutes=2)

        return cls.objects.create(
            sync_type=sync_type,
            source_model=source_model,
            source_id=source_id,
            source_repr=source_repr,
            error_message=error_message,
            error_traceback=traceback_str,
            context=context or {},
            next_retry_at=next_retry
        )

    def schedule_retry(self):
        """Programme un nouveau retry avec backoff exponentiel."""
        from django.utils import timezone
        from datetime import timedelta

        if self.retry_count >= self.max_retries:
            self.status = 'failed'
            self.save()
            return False

        # Backoff exponentiel: 2^(retry+1) minutes
        delay_minutes = 2 ** (self.retry_count + 1)
        self.retry_count += 1
        self.next_retry_at = timezone.now() + timedelta(minutes=delay_minutes)
        self.status = 'pending'
        self.save()
        return True

    def mark_resolved(self, admin_user=None):
        """Marque l'échec comme résolu."""
        from django.utils import timezone
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.resolved_by = admin_user
        self.save()

    def mark_ignored(self, admin_user=None):
        """Marque l'échec comme ignoré (ne plus retenter)."""
        from django.utils import timezone
        self.status = 'ignored'
        self.resolved_at = timezone.now()
        self.resolved_by = admin_user
        self.save()


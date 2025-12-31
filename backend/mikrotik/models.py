from django.db import models
from django.conf import settings


class MikrotikRouter(models.Model):
    """Mikrotik Router configuration"""
    name = models.CharField(
        max_length=255,
        help_text="Nom unique du routeur (ex: Router-Principal)"
    )
    host = models.CharField(
        max_length=255,
        help_text="Adresse IP ou hostname du routeur MikroTik"
    )
    port = models.IntegerField(
        default=8728,
        help_text="Port API MikroTik (8728 par défaut, 8729 pour SSL)"
    )
    username = models.CharField(
        max_length=255,
        help_text="Nom d'utilisateur pour l'API MikroTik"
    )
    password = models.CharField(
        max_length=255,
        help_text="Mot de passe API (stocké de manière sécurisée)"
    )
    use_ssl = models.BooleanField(
        default=False,
        help_text="Utiliser SSL/TLS pour la connexion API"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Activer/désactiver ce routeur pour la synchronisation"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Description optionnelle du routeur"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mikrotik_routers'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.host})"


class MikrotikHotspotUser(models.Model):
    """Mikrotik Hotspot User"""
    router = models.ForeignKey(MikrotikRouter, on_delete=models.CASCADE, related_name='hotspot_users')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mikrotik_accounts')

    # Hotspot user details
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    mac_address = models.CharField(max_length=17, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    # Limits
    uptime_limit = models.IntegerField(null=True, blank=True, help_text='Uptime limit in seconds')
    bytes_in_limit = models.BigIntegerField(null=True, blank=True)
    bytes_out_limit = models.BigIntegerField(null=True, blank=True)
    rate_limit = models.CharField(max_length=100, blank=True, null=True, help_text='e.g., 512k/2M')

    # Status
    is_active = models.BooleanField(default=True)
    is_disabled = models.BooleanField(default=False)

    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_sync = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'mikrotik_hotspot_users'
        ordering = ['-created_at']
        unique_together = ['router', 'username']

    def __str__(self):
        return f"{self.username} on {self.router.name}"


class MikrotikActiveConnection(models.Model):
    """Active connections on Mikrotik"""
    router = models.ForeignKey(MikrotikRouter, on_delete=models.CASCADE, related_name='active_connections')
    hotspot_user = models.ForeignKey(MikrotikHotspotUser, on_delete=models.SET_NULL, null=True, blank=True)

    # Connection details
    session_id = models.CharField(max_length=255, unique=True)
    username = models.CharField(max_length=255)
    mac_address = models.CharField(max_length=17, db_index=True)
    ip_address = models.GenericIPAddressField()

    # Statistics
    uptime = models.IntegerField(default=0)  # seconds
    bytes_in = models.BigIntegerField(default=0)
    bytes_out = models.BigIntegerField(default=0)
    packets_in = models.BigIntegerField(default=0)
    packets_out = models.BigIntegerField(default=0)

    # Timestamps
    login_time = models.DateTimeField()
    last_update = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mikrotik_active_connections'
        ordering = ['-login_time']
        indexes = [
            models.Index(fields=['router', 'mac_address']),
            models.Index(fields=['session_id']),
        ]

    def __str__(self):
        return f"{self.username} - {self.ip_address}"


class MikrotikLog(models.Model):
    """Mikrotik operation logs"""
    LOG_LEVEL_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('debug', 'Debug'),
    ]

    router = models.ForeignKey(MikrotikRouter, on_delete=models.CASCADE, related_name='logs')
    level = models.CharField(max_length=20, choices=LOG_LEVEL_CHOICES, default='info')
    operation = models.CharField(max_length=100)  # e.g., 'add_user', 'remove_user', 'sync'
    message = models.TextField()
    details = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mikrotik_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['router', 'created_at']),
            models.Index(fields=['level', 'created_at']),
        ]

    def __str__(self):
        return f"[{self.level.upper()}] {self.operation} - {self.router.name}"

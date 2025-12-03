from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta


class Promotion(models.Model):
    """Model for student promotions/classes"""
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nom de la promotion (ex: ING3, L1, M2, etc.)"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Description de la promotion"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Si la promotion est active et peut être sélectionnée"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'promotions'
        ordering = ['name']
        verbose_name = 'Promotion'
        verbose_name_plural = 'Promotions'

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Extended User model for captive portal users"""
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('user', 'User'),
    ]

    # Nouveaux champs pour le système d'inscription
    promotion = models.CharField(max_length=100, blank=True, null=True, help_text="Promotion de l'étudiant (ex: ING3, L1, etc.)")
    matricule = models.CharField(max_length=50, blank=True, null=True, help_text="Matricule de l'étudiant")
    is_radius_activated = models.BooleanField(default=False, help_text="Utilisateur activé dans RADIUS par un administrateur")

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
    """Blocked/Whitelisted sites management"""
    TYPE_CHOICES = [
        ('blacklist', 'Blacklist'),
        ('whitelist', 'Whitelist'),
    ]

    url = models.CharField(max_length=255, unique=True, db_index=True, help_text='Domain or URL to block/allow')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='blacklist')
    reason = models.CharField(max_length=255, blank=True, null=True, help_text='Reason for blocking/allowing')
    is_active = models.BooleanField(default=True)

    # Metadata
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='blocked_sites')
    added_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'blocked_sites'
        ordering = ['-added_date']
        indexes = [
            models.Index(fields=['type', 'is_active']),
        ]

    def __str__(self):
        return f"{self.url} ({self.type})"


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

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta


class Role(models.Model):
    """User roles for access control"""
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('user', 'User'),
    ]

    name = models.CharField(max_length=50, unique=True, choices=ROLE_CHOICES, db_index=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'roles'
        ordering = ['name']

    def __str__(self):
        return self.get_name_display()


def get_default_role():
    """Get or create the default 'user' role"""
    role, _ = Role.objects.get_or_create(
        name='user',
        defaults={'description': 'Standard user with basic access'}
    )
    return role.id


class User(AbstractUser):
    """Extended User model for captive portal users"""
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    mac_address = models.CharField(max_length=17, blank=True, null=True, db_index=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    is_voucher_user = models.BooleanField(default=False)
    voucher_code = models.CharField(max_length=50, blank=True, null=True)
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name='users', default=get_default_role)
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
        return self.is_staff or self.is_superuser or self.role.name == 'admin'

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

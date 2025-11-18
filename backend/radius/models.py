from django.db import models
from django.conf import settings


class RadiusServer(models.Model):
    """RADIUS Server configuration"""
    name = models.CharField(max_length=255)
    host = models.CharField(max_length=255)
    auth_port = models.IntegerField(default=1812)
    acct_port = models.IntegerField(default=1813)
    secret = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    timeout = models.IntegerField(default=5, help_text='Timeout in seconds')
    retries = models.IntegerField(default=3)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'radius_servers'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.host})"


class RadiusAuthLog(models.Model):
    """RADIUS Authentication logs"""
    STATUS_CHOICES = [
        ('accept', 'Accept'),
        ('reject', 'Reject'),
        ('challenge', 'Challenge'),
        ('error', 'Error'),
    ]

    server = models.ForeignKey(RadiusServer, on_delete=models.CASCADE, related_name='auth_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    # Authentication details
    username = models.CharField(max_length=255, db_index=True)
    mac_address = models.CharField(max_length=17, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    nas_ip_address = models.GenericIPAddressField(blank=True, null=True)
    nas_port = models.IntegerField(blank=True, null=True)

    # Result
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    reply_message = models.TextField(blank=True, null=True)

    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    request_data = models.JSONField(null=True, blank=True)
    response_data = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'radius_auth_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['username', 'timestamp']),
            models.Index(fields=['status', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.username} - {self.status} at {self.timestamp}"


class RadiusAccounting(models.Model):
    """RADIUS Accounting records"""
    STATUS_TYPE_CHOICES = [
        ('start', 'Start'),
        ('stop', 'Stop'),
        ('interim-update', 'Interim Update'),
        ('accounting-on', 'Accounting On'),
        ('accounting-off', 'Accounting Off'),
    ]

    TERMINATION_CAUSE_CHOICES = [
        ('user-request', 'User Request'),
        ('lost-carrier', 'Lost Carrier'),
        ('idle-timeout', 'Idle Timeout'),
        ('session-timeout', 'Session Timeout'),
        ('admin-reset', 'Admin Reset'),
        ('port-error', 'Port Error'),
        ('nas-error', 'NAS Error'),
        ('nas-request', 'NAS Request'),
        ('nas-reboot', 'NAS Reboot'),
    ]

    server = models.ForeignKey(RadiusServer, on_delete=models.CASCADE, related_name='accounting_records')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    # Session identification
    session_id = models.CharField(max_length=255, db_index=True)
    username = models.CharField(max_length=255, db_index=True)
    mac_address = models.CharField(max_length=17, blank=True, null=True)

    # Network details
    framed_ip_address = models.GenericIPAddressField(blank=True, null=True)
    nas_ip_address = models.GenericIPAddressField(blank=True, null=True)
    nas_port = models.IntegerField(blank=True, null=True)

    # Status
    status_type = models.CharField(max_length=20, choices=STATUS_TYPE_CHOICES)
    termination_cause = models.CharField(max_length=50, choices=TERMINATION_CAUSE_CHOICES, blank=True, null=True)

    # Session timing
    session_time = models.IntegerField(default=0, help_text='Session duration in seconds')
    start_time = models.DateTimeField(null=True, blank=True)
    stop_time = models.DateTimeField(null=True, blank=True)

    # Data usage
    input_octets = models.BigIntegerField(default=0)
    output_octets = models.BigIntegerField(default=0)
    input_packets = models.BigIntegerField(default=0)
    output_packets = models.BigIntegerField(default=0)
    input_gigawords = models.BigIntegerField(default=0)
    output_gigawords = models.BigIntegerField(default=0)

    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    raw_data = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'radius_accounting'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['session_id', 'timestamp']),
            models.Index(fields=['username', 'timestamp']),
            models.Index(fields=['status_type', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.username} - {self.status_type} - {self.session_id}"

    @property
    def total_octets(self):
        """Calculate total data transferred including gigawords"""
        input_total = (self.input_gigawords * 4294967296) + self.input_octets
        output_total = (self.output_gigawords * 4294967296) + self.output_octets
        return input_total + output_total


class RadiusClient(models.Model):
    """RADIUS Network Access Server (NAS) clients"""
    name = models.CharField(max_length=255)
    shortname = models.CharField(max_length=50, unique=True)
    nas_type = models.CharField(max_length=50, default='other')

    # Network configuration
    ip_address = models.GenericIPAddressField(unique=True)
    secret = models.CharField(max_length=255)

    # Additional info
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'radius_clients'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.ip_address})"

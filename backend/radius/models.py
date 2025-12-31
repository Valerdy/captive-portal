from django.db import models
from django.conf import settings


class RadiusServer(models.Model):
    """RADIUS Server configuration"""
    name = models.CharField(
        max_length=255,
        help_text="Nom unique du serveur RADIUS (ex: FreeRADIUS-Principal)"
    )
    host = models.CharField(
        max_length=255,
        help_text="Adresse IP ou hostname du serveur RADIUS"
    )
    auth_port = models.IntegerField(
        default=1812,
        help_text="Port d'authentification RADIUS (1812 par défaut)"
    )
    acct_port = models.IntegerField(
        default=1813,
        help_text="Port d'accounting RADIUS (1813 par défaut)"
    )
    secret = models.CharField(
        max_length=255,
        help_text="Secret partagé RADIUS (stocké de manière sécurisée)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Activer/désactiver ce serveur RADIUS"
    )
    timeout = models.IntegerField(
        default=5,
        help_text="Délai d'attente en secondes avant timeout"
    )
    retries = models.IntegerField(
        default=3,
        help_text="Nombre de tentatives en cas d'échec"
    )

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


# ============================================================================
# FreeRADIUS Tables - Standard Schema for User Authentication
# ============================================================================

class RadCheck(models.Model):
    """
    FreeRADIUS radcheck table - User authentication credentials
    Stores username and password for RADIUS authentication
    """
    username = models.CharField(max_length=64, db_index=True)
    attribute = models.CharField(max_length=64, default='Cleartext-Password')
    op = models.CharField(max_length=2, default=':=')
    value = models.CharField(max_length=253)
    statut = models.BooleanField(default=True, help_text="1 = actif, 0 = désactivé")
    quota = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Quota de données en octets (ex: 53687091200 = 50 Go). NULL = illimité"
    )

    class Meta:
        db_table = 'radcheck'
        ordering = ['username']
        indexes = [
            models.Index(fields=['username', 'attribute']),
        ]

    def __str__(self):
        return f"{self.username} - {self.attribute} ({'activé' if self.statut else 'désactivé'})"


class RadReply(models.Model):
    """
    FreeRADIUS radreply table - User-specific reply attributes
    Contains attributes returned to NAS for specific users (e.g., Session-Timeout, bandwidth limits)
    """
    username = models.CharField(max_length=64, db_index=True)
    attribute = models.CharField(max_length=64)
    op = models.CharField(max_length=2, default='=')
    value = models.CharField(max_length=253)

    class Meta:
        db_table = 'radreply'
        ordering = ['username']
        indexes = [
            models.Index(fields=['username', 'attribute']),
        ]

    def __str__(self):
        return f"{self.username} - {self.attribute}: {self.value}"


class RadGroupCheck(models.Model):
    """
    FreeRADIUS radgroupcheck table - Group-level authentication checks
    Defines authentication parameters for user groups
    """
    groupname = models.CharField(max_length=64, db_index=True)
    attribute = models.CharField(max_length=64)
    op = models.CharField(max_length=2, default=':=')
    value = models.CharField(max_length=253)

    class Meta:
        managed = False  # Table gérée par FreeRADIUS, pas par Django
        db_table = 'radgroupcheck'
        ordering = ['groupname']

    def __str__(self):
        return f"{self.groupname} - {self.attribute}"


class RadGroupReply(models.Model):
    """
    FreeRADIUS radgroupreply table - Group-level reply attributes
    Contains attributes returned to NAS for group members

    Note: Le schéma FreeRADIUS standard n'inclut PAS de colonne 'priority'.
    Ce modèle est compatible avec le schéma standard (sans priority).
    """
    groupname = models.CharField(max_length=64, db_index=True)
    attribute = models.CharField(max_length=64)
    op = models.CharField(max_length=2, default='=')
    value = models.CharField(max_length=253)

    class Meta:
        managed = False  # Table gérée par FreeRADIUS, pas par Django
        db_table = 'radgroupreply'
        ordering = ['groupname']
        indexes = [
            models.Index(fields=['groupname', 'attribute']),
        ]

    def __str__(self):
        return f"{self.groupname} - {self.attribute}: {self.value}"


class RadUserGroup(models.Model):
    """
    FreeRADIUS radusergroup table - User to group mapping
    Associates users with groups for applying group-level policies
    """
    username = models.CharField(max_length=64, db_index=True)
    groupname = models.CharField(max_length=64, db_index=True)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = 'radusergroup'
        ordering = ['username', 'priority']
        unique_together = ('username', 'groupname')
        indexes = [
            models.Index(fields=['username', 'priority']),
            models.Index(fields=['groupname']),
        ]

    def __str__(self):
        return f"{self.username} -> {self.groupname}"


class RadPostAuth(models.Model):
    """
    FreeRADIUS radpostauth table - Post-authentication logging
    Logs all authentication attempts (success and failure)
    """
    username = models.CharField(max_length=64, db_index=True)
    pass_field = models.CharField('pass', max_length=64, db_column='pass')
    reply = models.CharField(max_length=32)
    authdate = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'radpostauth'
        ordering = ['-authdate']
        indexes = [
            models.Index(fields=['username', '-authdate']),
        ]

    def __str__(self):
        return f"{self.username} - {self.reply} at {self.authdate}"


class RadAcct(models.Model):
    """
    FreeRADIUS radacct table - Accounting and session data
    Stores detailed information about user sessions including data usage
    """
    radacctid = models.BigAutoField(primary_key=True, db_column='radacctid')
    acctsessionid = models.CharField(max_length=64, db_index=True, db_column='acctsessionid')
    acctuniqueid = models.CharField(max_length=32, unique=True, db_column='acctuniqueid')
    username = models.CharField(max_length=64, db_index=True)

    # NAS information
    nasipaddress = models.GenericIPAddressField(db_column='nasipaddress')
    nasportid = models.CharField(max_length=15, blank=True, null=True, db_column='nasportid')
    nasporttype = models.CharField(max_length=32, blank=True, null=True, db_column='nasporttype')

    # Session timing
    acctstarttime = models.DateTimeField(null=True, blank=True, db_index=True, db_column='acctstarttime')
    acctupdatetime = models.DateTimeField(null=True, blank=True, db_column='acctupdatetime')
    acctstoptime = models.DateTimeField(null=True, blank=True, db_index=True, db_column='acctstoptime')
    acctsessiontime = models.IntegerField(null=True, blank=True, db_column='acctsessiontime', help_text='Session duration in seconds')

    # Authentication type
    acctauthentic = models.CharField(max_length=32, blank=True, null=True, db_column='acctauthentic')

    # Connection info
    connectinfo_start = models.CharField(max_length=50, blank=True, null=True, db_column='connectinfo_start')
    connectinfo_stop = models.CharField(max_length=50, blank=True, null=True, db_column='connectinfo_stop')

    # Data usage - INPUT (Download)
    acctinputoctets = models.BigIntegerField(null=True, blank=True, default=0, db_column='acctinputoctets')
    acctoutputoctets = models.BigIntegerField(null=True, blank=True, default=0, db_column='acctoutputoctets')

    # Called and Calling Station ID (MAC addresses)
    calledstationid = models.CharField(max_length=50, blank=True, null=True, db_column='calledstationid')
    callingstationid = models.CharField(max_length=50, blank=True, null=True, db_column='callingstationid')

    # Termination
    acctterminatecause = models.CharField(max_length=32, blank=True, null=True, db_column='acctterminatecause')

    # Service type
    servicetype = models.CharField(max_length=32, blank=True, null=True, db_column='servicetype')

    # Framed protocol and IP
    framedprotocol = models.CharField(max_length=32, blank=True, null=True, db_column='framedprotocol')
    framedipaddress = models.GenericIPAddressField(null=True, blank=True, db_index=True, db_column='framedipaddress')

    class Meta:
        managed = False  # Table gérée par FreeRADIUS, pas par Django
        db_table = 'radacct'
        ordering = ['-acctstarttime']
        indexes = [
            models.Index(fields=['username', '-acctstarttime']),
            models.Index(fields=['acctsessionid']),
            models.Index(fields=['framedipaddress']),
            models.Index(fields=['nasipaddress']),
        ]

    def __str__(self):
        return f"{self.username} - {self.acctsessionid}"

    @property
    def total_octets(self):
        """Calculate total data transferred (input + output)"""
        input_octets = self.acctinputoctets or 0
        output_octets = self.acctoutputoctets or 0
        return input_octets + output_octets

    @property
    def total_input(self):
        """Total download in bytes"""
        return self.acctinputoctets or 0

    @property
    def total_output(self):
        """Total upload in bytes"""
        return self.acctoutputoctets or 0

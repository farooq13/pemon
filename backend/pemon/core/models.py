import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    Abstract base model that provides self-updating created_at and updated_at fields.
    
    All models in the application should inherit from this to maintain
    consistent timestamp tracking.
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Timestamp when this record was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when this record was last updated"
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']


class UUIDModel(models.Model):
    """
    Abstract base model that uses UUID as primary key.
    
    Using UUID instead of auto-incrementing integers provides:
    - Better security (no sequential ID guessing)
    - Distributed system compatibility
    - Easier data migration between databases
    
    Attributes:
        id (UUIDField): Primary key using UUID4
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for this record"
    )

    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimeStampedModel):
    """
    Base model combining UUID primary key and timestamp fields.
    
    This is the recommended base class for all models in the application.
    It provides:
    - UUID primary key for security
    - Automatic timestamp tracking
    - Soft delete capability
    """
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Indicates if this record has been soft-deleted"
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when this record was deleted"
    )

    class Meta:
        abstract = True

    def soft_delete(self):
        """
        Soft delete this record by setting is_deleted flag and deleted_at timestamp.
        
        This method marks the record as deleted without actually removing it from
        the database, allowing for data recovery and audit trails.
        
        Returns:
            bool: True if the record was successfully soft-deleted
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
        return True

    def restore(self):
        """
        Restore a soft-deleted record.
        
        Returns:
            bool: True if the record was successfully restored
        """
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
        return True


class AuditLog(BaseModel):
    """
    Model for tracking critical actions and changes in the system.
    
    This model stores an audit trail of important operations for:
    - Security monitoring
    - Compliance reporting
    - Debugging and troubleshooting
    - Fraud detection
    """
    
    class ActionType(models.TextChoices):
        CREATE = 'CREATE', 'Create'
        UPDATE = 'UPDATE', 'Update'
        DELETE = 'DELETE', 'Delete'
        LOGIN = 'LOGIN', 'Login'
        LOGOUT = 'LOGOUT', 'Logout'
        TRANSACTION = 'TRANSACTION', 'Transaction'
        KYC_SUBMIT = 'KYC_SUBMIT', 'KYC Submission'
        KYC_APPROVE = 'KYC_APPROVE', 'KYC Approval'
        KYC_REJECT = 'KYC_REJECT', 'KYC Rejection'
        WALLET_FREEZE = 'WALLET_FREEZE', 'Wallet Freeze'
        WALLET_UNFREEZE = 'WALLET_UNFREEZE', 'Wallet Unfreeze'
        PASSWORD_CHANGE = 'PASSWORD_CHANGE', 'Password Change'
        PASSWORD_RESET = 'PASSWORD_RESET', 'Password Reset'
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text="User who performed this action"
    )
    action = models.CharField(
        max_length=50,
        choices=ActionType.choices,
        db_index=True,
        help_text="Type of action performed"
    )
    model_name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Name of the model affected by this action"
    )
    object_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="ID of the object affected"
    )
    changes = models.JSONField(
        default=dict,
        blank=True,
        help_text="Dictionary of changes made (field: {old: value, new: value})"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address from which the action was performed"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent string of the client"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata about this action"
    )

    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'action', 'created_at']),
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['action', 'created_at']),
        ]

    def __str__(self):
        username = self.user.email if self.user else 'System'
        return f"{username} - {self.action} - {self.model_name} - {self.created_at}"


class SystemConfiguration(BaseModel):
    """
    Model for storing system-wide configuration settings.
    
    This model allows dynamic configuration of system settings without
    requiring code changes or server restarts.
    
    Attributes:
        key (CharField): Unique configuration key
        value (TextField): Configuration value (can be JSON string)
        description (TextField): Human-readable description of this setting
        is_active (BooleanField): Whether this configuration is active
    """
    key = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Unique configuration key"
    )
    value = models.TextField(
        help_text="Configuration value (can be JSON string for complex data)"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of what this configuration does"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this configuration is currently active"
    )

    class Meta:
        verbose_name = 'System Configuration'
        verbose_name_plural = 'System Configurations'
        ordering = ['key']

    def __str__(self):
        return f"{self.key}: {self.value[:50]}"


class AppVersion(BaseModel):
    """
    Model for tracking mobile app versions and enforcing updates.
    
    Attributes:
        platform (CharField): Platform (iOS/Android)
        version_number (CharField): Version number (e.g., 1.0.0)
        build_number (IntegerField): Build number
        minimum_supported_version (CharField): Minimum version that's still supported
        is_force_update (BooleanField): Whether this version requires forced update
        release_notes (TextField): Release notes for this version
        download_url (URLField): URL to download this version
    """
    
    class Platform(models.TextChoices):
        IOS = 'IOS', 'iOS'
        ANDROID = 'ANDROID', 'Android'
    
    platform = models.CharField(
        max_length=20,
        choices=Platform.choices,
        help_text="Platform for this version"
    )
    version_number = models.CharField(
        max_length=20,
        help_text="Version number (e.g., 1.0.0)"
    )
    build_number = models.IntegerField(
        help_text="Build number"
    )
    minimum_supported_version = models.CharField(
        max_length=20,
        help_text="Minimum version that's still supported"
    )
    is_force_update = models.BooleanField(
        default=False,
        help_text="Whether users must update to this version"
    )
    release_notes = models.TextField(
        blank=True,
        help_text="What's new in this version"
    )
    download_url = models.URLField(
        help_text="URL to download this version"
    )

    class Meta:
        verbose_name = 'App Version'
        verbose_name_plural = 'App Versions'
        ordering = ['-build_number']
        unique_together = [['platform', 'version_number']]

    def __str__(self):
        return f"{self.platform} v{self.version_number} (Build {self.build_number})"

class Notification(BaseModel):
    """
    Model for System and Transactional Notifications.
    """
    class NotificationType(models.TextChoices):
        SYSTEM = 'SYSTEM', 'System Alert'
        TRANSACTION_RECEIVED = 'TRANSACTION_RECEIVED', 'Money Received'
        ACCOUNT_UPDATE = 'ACCOUNT_UPDATE', 'Account Update'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="User this notification belongs to"
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM
    )
    is_read = models.BooleanField(default=False)
    related_entity_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.email} - {self.title}"
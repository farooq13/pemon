import uuid

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

from core.models import BaseModel


class KYC(BaseModel):
    """
    KYC verification model for user identity verification.
    
    Supports 4 tier levels:
    - Tier 0: Unverified (can't transact)
    - Tier 1: Basic KYC (limited transactions)
    - Tier 2: Intermediate KYC (higher limits)
    - Tier 3: Full KYC (unlimited transactions)
    
    """
    
    class TierLevel(models.IntegerChoices):
        TIER_0 = 0, 'Unverified'
        TIER_1 = 1, 'Basic KYC'
        TIER_2 = 2, 'Intermediate KYC'
        TIER_3 = 3, 'Full KYC'
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Review'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        EXPIRED = 'EXPIRED', 'Expired'
    
    class IDType(models.TextChoices):
        NIN = 'NIN', 'National ID Card'
        DRIVERS_LICENSE = 'DRIVERS_LICENSE', 'Driver\'s License'
        VOTERS_CARD = 'VOTERS_CARD', 'Voter\'s Card'
        INTERNATIONAL_PASSPORT = 'INTERNATIONAL_PASSPORT', 'International Passport'
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='kyc',
        help_text='User this KYC belongs to'
    )
    
    tier = models.IntegerField(
        choices=TierLevel.choices,
        default=TierLevel.TIER_0,
        db_index=True,
        help_text='Current KYC verification tier'
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        help_text='Current verification status'
    )
    
    # Personal Information
    bvn_validator = RegexValidator(
        regex=r'^\d{11}$',
        message='BVN must be exactly 11 digits'
    )
    bvn = models.CharField(
        max_length=11,
        validators=[bvn_validator],
        blank=True,
        help_text='Bank Verification Number (11 digits)'
    )
    
    nin_validator = RegexValidator(
        regex=r'^\d{11}$',
        message='NIN must be exactly 11 digits'
    )
    nin = models.CharField(
        max_length=11,
        validators=[nin_validator],
        blank=True,
        help_text='National Identification Number (11 digits)'
    )
    
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text='Date of birth'
    )
    
    # Address Information
    address = models.TextField(
        blank=True,
        help_text='Residential address'
    )
    
    city = models.CharField(
        max_length=100,
        blank=True,
        help_text='City'
    )
    
    state = models.CharField(
        max_length=100,
        blank=True,
        help_text='State'
    )
    
    # ID Document
    id_type = models.CharField(
        max_length=50,
        choices=IDType.choices,
        blank=True,
        help_text='Type of ID document'
    )
    
    id_number = models.CharField(
        max_length=50,
        blank=True,
        help_text='ID document number'
    )
    
    id_document = models.FileField(
        upload_to='kyc/documents/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text='Uploaded ID document (PDF or image)'
    )
    
    selfie = models.ImageField(
        upload_to='kyc/selfies/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text='Selfie photo for verification'
    )
    
    # Verification Details
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='kyc_verifications',
        help_text='Admin who verified this KYC'
    )
    
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When this KYC was verified'
    )
    
    rejection_reason = models.TextField(
        blank=True,
        help_text='Reason for rejection (if rejected)'
    )
    
    # Additional metadata
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When KYC was first submitted'
    )
    
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When this KYC verification expires (for periodic re-verification)'
    )

    class Meta:
        verbose_name = 'KYC Verification'
        verbose_name_plural = 'KYC Verifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['tier', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - Tier {self.tier} ({self.get_status_display()})"

    def get_tier_limits(self):
        """
        Get transaction limits for current tier.
        
        Returns:
            dict: Transaction limits for this tier
        """
        from .tier_limits import TIER_LIMITS
        return TIER_LIMITS.get(self.tier, TIER_LIMITS[0])

    def can_transact(self, amount):
        """
        Check if user can perform a transaction of given amount.
        
        Args:
            amount (Decimal): Transaction amount to check
            
        Returns:
            tuple: (can_transact: bool, reason: str)
        """
        if self.status != self.Status.APPROVED:
            return False, 'KYC verification not approved'
        
        limits = self.get_tier_limits()
        
        if amount > limits['single_transaction_limit']:
            return False, f'Amount exceeds single transaction limit of ₦{limits["single_transaction_limit"]:,.2f}'
        
        return True, ''

    def approve(self, verified_by, tier=TierLevel.TIER_1):
        """
        Approve KYC and set tier level.
        
        Args:
            verified_by (User): Admin approving the KYC
            tier (int): Tier level to assign (default: 1)
        """
        from django.utils import timezone
        
        self.status = self.Status.APPROVED
        self.tier = tier
        self.verified_by = verified_by
        self.verified_at = timezone.now()
        self.save(update_fields=['status', 'tier', 'verified_by', 'verified_at', 'updated_at'])

    def reject(self, verified_by, reason):
        """
        Reject KYC with reason.
        
        Args:
            verified_by (User): Admin rejecting the KYC
            reason (str): Reason for rejection
        """
        from django.utils import timezone
        
        self.status = self.Status.REJECTED
        self.verified_by = verified_by
        self.verified_at = timezone.now()
        self.rejection_reason = reason
        self.save(update_fields=['status', 'verified_by', 'verified_at', 'rejection_reason', 'updated_at'])

    def submit(self):
        """Mark KYC as submitted for review."""
        from django.utils import timezone
        
        if not self.submitted_at:
            self.submitted_at = timezone.now()
        
        self.status = self.Status.PENDING
        self.save(update_fields=['status', 'submitted_at', 'updated_at'])


class KYCDocument(BaseModel):
    """
    Additional documents that can be uploaded for KYC verification.
    
    Allows users to submit multiple documents for higher tier verification.
    
    """
    
    class DocumentType(models.TextChoices):
        UTILITY_BILL = 'UTILITY_BILL', 'Utility Bill'
        BANK_STATEMENT = 'BANK_STATEMENT', 'Bank Statement'
        EMPLOYMENT_LETTER = 'EMPLOYMENT_LETTER', 'Employment Letter'
        TAX_DOCUMENT = 'TAX_DOCUMENT', 'Tax Document'
        BUSINESS_LICENSE = 'BUSINESS_LICENSE', 'Business License'
        OTHER = 'OTHER', 'Other'
    
    kyc = models.ForeignKey(
        KYC,
        on_delete=models.CASCADE,
        related_name='additional_documents',
        help_text='Associated KYC record'
    )
    
    document_type = models.CharField(
        max_length=50,
        choices=DocumentType.choices,
        help_text='Type of document'
    )
    
    document = models.FileField(
        upload_to='kyc/additional_documents/%Y/%m/%d/',
        help_text='Uploaded document file'
    )
    
    notes = models.TextField(
        blank=True,
        help_text='Additional notes about this document'
    )

    class Meta:
        verbose_name = 'KYC Document'
        verbose_name_plural = 'KYC Documents'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.kyc.user.email} - {self.get_document_type_display()}"
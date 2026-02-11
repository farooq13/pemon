import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()


class Wallet(models.Model):
    """
    User wallet model.
    
    Each verified user gets one wallet for storing and managing funds.
    Wallets are created automatically when KYC is approved.
    
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    user = models.OneToOneField(
        User,
        on_delete=models.PROTECT,  # Never delete users with wallets
        related_name='wallet',
        db_index=True
    )
    
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Current wallet balance'
    )
    
    virtual_account_number = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        help_text='Unique virtual account number for deposits'
    )
    
    is_frozen = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Whether wallet is frozen (cannot send money)'
    )
    
    freeze_reason = models.TextField(
        blank=True,
        default='',
        help_text='Reason for freezing the wallet'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'wallets'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['virtual_account_number']),
            models.Index(fields=['-created_at']),
        ]
        constraints = [
            # Balance must be non-negative
            models.CheckConstraint(
                check=models.Q(balance__gte=0),
                name='wallet_balance_non_negative'
            ),
            # Virtual account number must be 10 digits
            models.CheckConstraint(
                check=models.Q(virtual_account_number__regex=r'^\d{10}$'),
                name='virtual_account_10_digits'
            ),
        ]
    
    def __str__(self):
        return f"Wallet - {self.user.email} (₦{self.balance:,.2f})"
    
    def clean(self):
        """
        Model-level validation.
        """
        super().clean()
        
        # Validate balance is non-negative
        if self.balance is not None and self.balance < 0:
            raise ValidationError({
                'balance': 'Balance cannot be negative'
            })
        
        # Validate virtual account number format
        if self.virtual_account_number:
            if not self.virtual_account_number.isdigit():
                raise ValidationError({
                    'virtual_account_number': 'Virtual account number must contain only digits'
                })
            
            if len(self.virtual_account_number) != 10:
                raise ValidationError({
                    'virtual_account_number': 'Virtual account number must be exactly 10 digits'
                })
    
    def save(self, *args, **kwargs):
        """
        Override save to run validation.
        """
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        """Check if wallet is active (not frozen)."""
        return not self.is_frozen
    
    @property
    def formatted_balance(self):
        """Get formatted balance with currency symbol."""
        return f"₦{self.balance:,.2f}"
    
    @property
    def can_send_money(self):
        """Check if wallet can send money (not frozen)."""
        return not self.is_frozen
    
    @property
    def can_receive_money(self):
        """Check if wallet can receive money (always true for now)."""
        return True
    
    def get_available_balance(self):
        """
        Get available balance for transactions.
        
        For future use if we implement pending/reserved amounts.
        Currently returns the full balance.
        
        Returns:
            Decimal: Available balance
        """
        return self.balance
    
    def has_sufficient_balance(self, amount: Decimal) -> bool:
        """
        Check if wallet has sufficient balance for a transaction.
        
        Args:
            amount: Amount to check
            
        Returns:
            bool: True if sufficient balance exists
        """
        return self.get_available_balance() >= amount
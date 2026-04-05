import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()


class TransactionType(models.TextChoices):
    """
    Enumeration of all possible transaction types.
    """
    DEPOSIT = 'DEPOSIT', 'Deposit'
    WITHDRAWAL = 'WITHDRAWAL', 'Withdrawal'
    TRANSFER = 'TRANSFER', 'P2P Transfer'
    BILL_PAYMENT = 'BILL_PAYMENT', 'Bill Payment'
    AIRTIME = 'AIRTIME', 'Airtime Purchase'
    DATA = 'DATA', 'Data Purchase'
    ELECTRICITY = 'ELECTRICITY', 'Electricity Payment'
    CABLE_TV = 'CABLE_TV', 'Cable TV Subscription'
    REVERSAL = 'REVERSAL', 'Transaction Reversal'
    REFUND = 'REFUND', 'Refund'
    COMMISSION = 'COMMISSION', 'Commission'
    CHARGE = 'CHARGE', 'Service Charge'


class TransactionStatus(models.TextChoices):
    """
    Transaction status lifecycle.
    """
    PENDING = 'PENDING', 'Pending'
    PROCESSING = 'PROCESSING', 'Processing'
    COMPLETED = 'COMPLETED', 'Completed'
    FAILED = 'FAILED', 'Failed'
    REVERSED = 'REVERSED', 'Reversed'


class EntryType(models.TextChoices):
    """
    Ledger entry types for double-entry bookkeeping.
    """
    DEBIT = 'DEBIT', 'Debit'
    CREDIT = 'CREDIT', 'Credit'


class Transaction(models.Model):
    """
    Main transaction record.
    
    Represents a financial transaction with immutable records.
    Each transaction links to multiple ledger entries for double-entry accounting.
    
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,  # Never delete users with transactions
        related_name='transactions',
        db_index=True
    )
    
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        db_index=True
    )
    
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Transaction amount (must be positive)'
    )
    
    status = models.CharField(
        max_length=15,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
        db_index=True
    )
    
    reference = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text='Unique transaction reference'
    )
    
    idempotency_key = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text='Key to prevent duplicate transactions'
    )
    
    description = models.TextField(
        blank=True,
        help_text='Transaction description or note'
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional transaction data'
    )
    
    # For transfers, link to recipient
    recipient = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='received_transactions',
        null=True,
        blank=True,
        db_index=True
    )
    
    # Reversal tracking
    reversed_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reverses',
        help_text='Reversal transaction if this was reversed'
    )
    
    original_transaction = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reversals',
        help_text='Original transaction if this is a reversal'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['transaction_type', '-created_at']),
        ]
        constraints = [
            # Amount must be positive
            models.CheckConstraint(
                check=models.Q(amount__gt=0),
                name='transaction_amount_positive'
            ),
            # Transfers must have a recipient
            models.CheckConstraint(
                check=(
                    ~models.Q(transaction_type='TRANSFER') |
                    models.Q(recipient__isnull=False)
                ),
                name='transfer_has_recipient'
            ),
        ]
    
    def __str__(self):
        return f"{self.reference} - {self.transaction_type} - ₦{self.amount}"
    
    def clean(self):
        """
        Model-level validation.
        """
        super().clean()
        
        # Validate amount is positive
        if self.amount and self.amount <= 0:
            raise ValidationError({
                'amount': 'Amount must be greater than zero'
            })
        
        # Validate transfer has recipient
        if self.transaction_type == TransactionType.TRANSFER:
            if not self.recipient:
                raise ValidationError({
                    'recipient': 'Transfer transaction must have a recipient'
                })
            
            # User cannot transfer to themselves
            if self.user_id == self.recipient_id:
                raise ValidationError({
                    'recipient': 'Cannot transfer money to yourself'
                })
    
    def save(self, *args, **kwargs):
        """
        Override save to run validation.
        """
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_completed(self):
        """Check if transaction is completed."""
        return self.status == TransactionStatus.COMPLETED
    
    @property
    def is_pending(self):
        """Check if transaction is pending."""
        return self.status == TransactionStatus.PENDING
    
    @property
    def is_reversed(self):
        """Check if transaction has been reversed."""
        return self.status == TransactionStatus.REVERSED or self.reversed_by is not None
    
    @property
    def can_be_reversed(self):
        """
        Check if transaction can be reversed.
        
        Only completed transactions that haven't been reversed can be reversed.
        """
        return (
            self.status == TransactionStatus.COMPLETED and
            self.reversed_by is None and
            self.transaction_type not in [
                TransactionType.REVERSAL,
                TransactionType.COMMISSION,
            ]
        )


class LedgerEntry(models.Model):
    """
    Individual ledger entry for double-entry bookkeeping.
    
    Every transaction creates at least 2 ledger entries:
    - One DEBIT entry (money leaving)
    - One CREDIT entry (money entering)
    
    The sum of all DEBIT entries must equal the sum of all CREDIT entries.
    
    Attributes:
        transaction: Parent transaction
        wallet: Wallet affected by this entry
        entry_type: DEBIT or CREDIT
        amount: Entry amount (always positive)
        balance_after: Wallet balance after this entry
        description: Entry description
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.PROTECT,
        related_name='ledger_entries',
        db_index=True
    )
    
    wallet = models.ForeignKey(
        'wallets.Wallet',
        on_delete=models.PROTECT,
        related_name='ledger_entries',
        db_index=True
    )
    
    entry_type = models.CharField(
        max_length=6,
        choices=EntryType.choices,
        db_index=True
    )
    
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Entry amount (always positive)'
    )
    
    balance_before = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Wallet balance before this entry'
    )
    
    balance_after = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Wallet balance after this entry'
    )
    
    description = models.TextField(
        blank=True,
        help_text='Entry description'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'ledger_entries'
        verbose_name_plural = 'Ledger entries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['wallet', '-created_at']),
            models.Index(fields=['transaction', 'entry_type']),
        ]
        constraints = [
            # Amount must be positive
            models.CheckConstraint(
                check=models.Q(amount__gt=0),
                name='ledger_amount_positive'
            ),
            # Balance after debit should be less than balance before
            # Balance after credit should be more than balance before
            # (This is enforced in service layer, not DB)
        ]
    
    def __str__(self):
        return f"{self.entry_type} - ₦{self.amount} - {self.wallet.user.email}"
    
    def clean(self):
        """
        Model-level validation.
        """
        super().clean()
        
        # Validate amount is positive
        if self.amount and self.amount <= 0:
            raise ValidationError({
                'amount': 'Amount must be greater than zero'
            })
        
        # Validate balance calculations
        if self.entry_type == EntryType.DEBIT:
            # Debit decreases balance
            expected_balance = self.balance_before - self.amount
            if abs(self.balance_after - expected_balance) > Decimal('0.001'):
                raise ValidationError({
                    'balance_after': f'Incorrect balance calculation for DEBIT. '
                                   f'Expected {expected_balance}, got {self.balance_after}'
                })
        elif self.entry_type == EntryType.CREDIT:
            # Credit increases balance
            expected_balance = self.balance_before + self.amount
            if abs(self.balance_after - expected_balance) > Decimal('0.001'):
                raise ValidationError({
                    'balance_after': f'Incorrect balance calculation for CREDIT. '
                                   f'Expected {expected_balance}, got {self.balance_after}'
                })
    
        def save(self, *args, **kwargs):
            # Check if record exists in database (not just if pk is set)
            creating = self._state.adding
            
            if not creating:  # This is an update
                raise ValidationError(
                    "Ledger entries are immutable and cannot be updated. "
                    "Create a reversal transaction instead."
                )
            
            super().save(*args, **kwargs)
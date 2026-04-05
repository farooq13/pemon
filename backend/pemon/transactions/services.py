import logging
from decimal import Decimal
from typing import Optional, Dict, Any, List
from datetime import datetime

from django.db import transaction, models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import (
    Transaction,
    LedgerEntry,
    TransactionType,
    TransactionStatus,
    EntryType
)
from .utils import (
    generate_transaction_reference,
    generate_idempotency_key,
    validate_transaction_amount
)
from wallets.models import Wallet

User = get_user_model()
logger = logging.getLogger(__name__)


class LedgerService:
    """
    Service class for ledger operations.
    
    Handles all transaction processing with double-entry bookkeeping,
    ensuring financial integrity and atomicity.
    """
    
    @staticmethod
    @transaction.atomic
    def create_transaction(
        user: User,
        transaction_type: str,
        amount: Decimal,
        description: str = "",
        recipient: Optional[User] = None,
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> Transaction:
        """
        Create a new transaction with ledger entries.
        
        This is the main entry point for all transaction creation.
        It ensures double-entry bookkeeping is maintained.
        
        Args:
            user: User initiating the transaction
            transaction_type: Type of transaction
            amount: Transaction amount
            description: Transaction description
            recipient: Recipient user (for transfers)
            metadata: Additional transaction data
            idempotency_key: Key to prevent duplicates
            
        Returns:
            Transaction: Created transaction
            
        Raises:
            ValidationError: If transaction invalid or duplicate
            
        """
        # Validate amount
        is_valid, error_msg = validate_transaction_amount(amount)
        if not is_valid:
            raise ValidationError(error_msg)
        
        # Check for duplicate (idempotency)
        if idempotency_key:
            existing_txn = Transaction.objects.filter(
                idempotency_key=idempotency_key
            ).first()
            
            if existing_txn:
                logger.warning(
                    f"Duplicate transaction attempt. "
                    f"Idempotency key: {idempotency_key}"
                )
                return existing_txn
        
        # Generate reference
        reference = generate_transaction_reference()
        
        # Create transaction record
        txn = Transaction.objects.create(
            user=user,
            transaction_type=transaction_type,
            amount=amount,
            status=TransactionStatus.PENDING,
            reference=reference,
            idempotency_key=idempotency_key,
            description=description,
            recipient=recipient,
            metadata=metadata or {}
        )
        
        logger.info(
            f"Created transaction {txn.reference} - "
            f"{transaction_type} - ₦{amount} - User: {user.id}"
        )
        
        return txn
    
    @staticmethod
    @transaction.atomic
    def process_debit(
        txn: Transaction,
        wallet: Wallet,
        amount: Decimal,
        description: str = ""
    ) -> LedgerEntry:
        """
        Create a DEBIT ledger entry (money leaving wallet).
        
        Args:
            txn: Parent transaction
            wallet: Wallet to debit
            amount: Amount to debit
            description: Entry description
            
        Returns:
            LedgerEntry: Created debit entry
            
        Raises:
            ValidationError: If insufficient balance
        """
        # Lock wallet for update to prevent race conditions
        wallet = Wallet.objects.select_for_update().get(id=wallet.id)
        
        # Check if wallet is frozen
        if wallet.is_frozen:
            raise ValidationError(
                f"Wallet {wallet.id} is frozen and cannot process debits"
            )
        
        # Check sufficient balance
        if wallet.balance < amount:
            raise ValidationError(
                f"Insufficient balance. Available: ₦{wallet.balance}, "
                f"Required: ₦{amount}"
            )
        
        # Record balance before
        balance_before = wallet.balance
        
        # Update wallet balance
        wallet.balance -= amount
        wallet.save(update_fields=['balance', 'updated_at'])
        
        # Create ledger entry
        entry = LedgerEntry.objects.create(
            transaction=txn,
            wallet=wallet,
            entry_type=EntryType.DEBIT,
            amount=amount,
            balance_before=balance_before,
            balance_after=wallet.balance,
            description=description or f"Debit for {txn.transaction_type}"
        )
        
        logger.info(
            f"DEBIT: ₦{amount} from wallet {wallet.id} - "
            f"Balance: ₦{balance_before} → ₦{wallet.balance}"
        )
        
        return entry
    
    @staticmethod
    @transaction.atomic
    def process_credit(
        txn: Transaction,
        wallet: Wallet,
        amount: Decimal,
        description: str = ""
    ) -> LedgerEntry:
        """
        Create a CREDIT ledger entry (money entering wallet).
        
        Args:
            txn: Parent transaction
            wallet: Wallet to credit
            amount: Amount to credit
            description: Entry description
            
        Returns:
            LedgerEntry: Created credit entry
        """
        # Lock wallet for update
        wallet = Wallet.objects.select_for_update().get(id=wallet.id)
        
        # Record balance before
        balance_before = wallet.balance
        
        # Update wallet balance
        wallet.balance += amount
        wallet.save(update_fields=['balance', 'updated_at'])
        
        # Create ledger entry
        entry = LedgerEntry.objects.create(
            transaction=txn,
            wallet=wallet,
            entry_type=EntryType.CREDIT,
            amount=amount,
            balance_before=balance_before,
            balance_after=wallet.balance,
            description=description or f"Credit for {txn.transaction_type}"
        )
        
        logger.info(
            f"CREDIT: ₦{amount} to wallet {wallet.id} - "
            f"Balance: ₦{balance_before} → ₦{wallet.balance}"
        )
        
        # Create notification for recipient
        from core.models import Notification
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        notification = Notification.objects.create(
            user=wallet.user,
            title="Money Received",
            message=f"You received ₦{amount:,.2f}. {description}",
            notification_type=Notification.NotificationType.TRANSACTION_RECEIVED,
            related_entity_id=str(txn.id) if txn else None
        )
        
        # Send WebSocket notification
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"user_{wallet.user.id}".replace("-", "_"),
                {
                    'type': 'notification_message',
                    'data': {
                        'id': str(notification.id),
                        'title': notification.title,
                        'message': notification.message,
                        'type': notification.notification_type,
                        'created_at': notification.created_at.isoformat()
                    }
                }
            )
        
        return entry
    
    @staticmethod
    @transaction.atomic
    def complete_transaction(txn: Transaction) -> Transaction:
        """
        Mark transaction as completed.
        
        Args:
            txn: Transaction to complete
            
        Returns:
            Transaction: Updated transaction
        """
        txn.status = TransactionStatus.COMPLETED
        txn.completed_at = timezone.now()
        txn.save(update_fields=['status', 'completed_at', 'updated_at'])
        
        logger.info(f"Transaction {txn.reference} marked as COMPLETED")
        
        return txn
    
    @staticmethod
    @transaction.atomic
    def fail_transaction(txn: Transaction, reason: str = "") -> Transaction:
        """
        Mark transaction as failed.
        
        Args:
            txn: Transaction to fail
            reason: Failure reason
            
        Returns:
            Transaction: Updated transaction
        """
        txn.status = TransactionStatus.FAILED
        
        if reason:
            txn.metadata['failure_reason'] = reason
        
        txn.save(update_fields=['status', 'metadata', 'updated_at'])
        
        logger.warning(
            f"Transaction {txn.reference} marked as FAILED. Reason: {reason}"
        )
        
        return txn
    
    @staticmethod
    @transaction.atomic
    def reverse_transaction(
        original_txn: Transaction,
        reversed_by_user: User,
        reason: str = ""
    ) -> Transaction:
        """
        Reverse a completed transaction.
        
        Creates a new reversal transaction that creates opposite
        ledger entries to undo the original transaction.
        
        Args:
            original_txn: Transaction to reverse
            reversed_by_user: User performing the reversal (usually admin)
            reason: Reversal reason
            
        Returns:
            Transaction: New reversal transaction
            
        Raises:
            ValidationError: If transaction cannot be reversed
        """
        # Validate transaction can be reversed
        if not original_txn.can_be_reversed:
            raise ValidationError(
                f"Transaction {original_txn.reference} cannot be reversed. "
                f"Status: {original_txn.status}, "
                f"Already reversed: {original_txn.is_reversed}"
            )
        
        # Create reversal transaction
        reversal_txn = Transaction.objects.create(
            user=original_txn.user,
            transaction_type=TransactionType.REVERSAL,
            amount=original_txn.amount,
            status=TransactionStatus.PENDING,
            reference=generate_transaction_reference(prefix="REV"),
            description=f"Reversal of {original_txn.reference}. Reason: {reason}",
            original_transaction=original_txn,
            metadata={
                'original_reference': original_txn.reference,
                'reversal_reason': reason,
                'reversed_by': str(reversed_by_user.id)
            }
        )
        
        # Get original ledger entries
        original_entries = original_txn.ledger_entries.all()
        
        # Create opposite entries
        for entry in original_entries:
            if entry.entry_type == EntryType.DEBIT:
                # Original was debit, so credit in reversal
                LedgerService.process_credit(
                    txn=reversal_txn,
                    wallet=entry.wallet,
                    amount=entry.amount,
                    description=f"Reversal credit for {original_txn.reference}"
                )
            else:
                # Original was credit, so debit in reversal
                LedgerService.process_debit(
                    txn=reversal_txn,
                    wallet=entry.wallet,
                    amount=entry.amount,
                    description=f"Reversal debit for {original_txn.reference}"
                )
        
        # Complete reversal transaction
        LedgerService.complete_transaction(reversal_txn)
        
        # Update original transaction
        original_txn.reversed_by = reversal_txn
        original_txn.status = TransactionStatus.REVERSED
        original_txn.save(update_fields=['reversed_by', 'status', 'updated_at'])
        
        logger.warning(
            f"Transaction {original_txn.reference} REVERSED by "
            f"user {reversed_by_user.id}. New reference: {reversal_txn.reference}"
        )
        
        return reversal_txn
    
    @staticmethod
    def verify_ledger_balance(txn: Transaction) -> bool:
        """
        Verify that ledger entries balance for a transaction.
        
        Sum of debits must equal sum of credits.
        
        Args:
            txn: Transaction to verify
            
        Returns:
            bool: True if balanced
        """
        entries = txn.ledger_entries.all()
        
        total_debits = sum(
            e.amount for e in entries if e.entry_type == EntryType.DEBIT
        )
        total_credits = sum(
            e.amount for e in entries if e.entry_type == EntryType.CREDIT
        )
        
        # Allow for small floating point differences
        is_balanced = abs(total_debits - total_credits) < Decimal('0.01')
        
        if not is_balanced:
            logger.error(
                f"LEDGER IMBALANCE for transaction {txn.reference}! "
                f"Debits: ₦{total_debits}, Credits: ₦{total_credits}"
            )
        
        return is_balanced
    
    @staticmethod
    def get_wallet_balance(wallet: Wallet) -> Decimal:
        """
        Calculate wallet balance from ledger entries.
        
        This is used for verification purposes to ensure
        the wallet balance matches the ledger.
        
        Args:
            wallet: Wallet to calculate balance for
            
        Returns:
            Decimal: Calculated balance
        """
        entries = LedgerEntry.objects.filter(wallet=wallet).order_by('created_at')
        
        balance = Decimal('0.00')
        
        for entry in entries:
            if entry.entry_type == EntryType.CREDIT:
                balance += entry.amount
            else:  # DEBIT
                balance -= entry.amount
        
        return balance
    
    @staticmethod
    def reconcile_wallet(wallet: Wallet) -> Dict[str, Any]:
        """
        Reconcile wallet balance with ledger entries.
        
        Compares wallet.balance with calculated balance from ledger.
        
        Args:
            wallet: Wallet to reconcile
            
        Returns:
            dict: Reconciliation results
        """
        calculated_balance = LedgerService.get_wallet_balance(wallet)
        current_balance = wallet.balance
        
        difference = current_balance - calculated_balance
        is_balanced = abs(difference) < Decimal('0.01')
        
        result = {
            'wallet_id': str(wallet.id),
            'current_balance': current_balance,
            'calculated_balance': calculated_balance,
            'difference': difference,
            'is_balanced': is_balanced,
        }
        
        if not is_balanced:
            logger.error(
                f"WALLET RECONCILIATION FAILED for wallet {wallet.id}! "
                f"Current: ₦{current_balance}, "
                f"Calculated: ₦{calculated_balance}, "
                f"Difference: ₦{difference}"
            )
        
        return result
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from transactions.models import (
    Transaction,
    LedgerEntry,
    TransactionType,
    TransactionStatus,
    EntryType
)
from transactions.services import LedgerService
from transactions.utils import (
    generate_transaction_reference,
    generate_idempotency_key,
    validate_transaction_amount
)
from wallets.models import Wallet
from wallets.services import WalletService

User = get_user_model()


class TransactionModelTests(TestCase):
    """Test suite for Transaction model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            phone_number='+2348012345678',
            password='testpass123'
        )
        
        self.recipient = User.objects.create_user(
            email='recipient@example.com',
            phone_number='+2348012345679',
            password='testpass123'
        )
    
    def test_transaction_creation(self):
        """Test creating a transaction."""
        txn = Transaction.objects.create(
            user=self.user,
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal('1000.00'),
            reference=generate_transaction_reference(),
            description='Test deposit'
        )
        
        self.assertIsNotNone(txn.id)
        self.assertEqual(txn.user, self.user)
        self.assertEqual(txn.amount, Decimal('1000.00'))
        self.assertEqual(txn.status, TransactionStatus.PENDING)
    
    def test_transfer_requires_recipient(self):
        """Test that transfer transactions require a recipient."""
        with self.assertRaises(ValidationError):
            txn = Transaction(
                user=self.user,
                transaction_type=TransactionType.TRANSFER,
                amount=Decimal('1000.00'),
                reference=generate_transaction_reference()
            )
            txn.save()
    
    def test_amount_must_be_positive(self):
        """Test that amount must be positive."""
        with self.assertRaises(ValidationError):
            txn = Transaction(
                user=self.user,
                transaction_type=TransactionType.DEPOSIT,
                amount=Decimal('-100.00'),
                reference=generate_transaction_reference()
            )
            txn.save()
    
    def test_cannot_transfer_to_self(self):
        """Test that user cannot transfer to themselves."""
        with self.assertRaises(ValidationError):
            txn = Transaction(
                user=self.user,
                transaction_type=TransactionType.TRANSFER,
                amount=Decimal('1000.00'),
                reference=generate_transaction_reference(),
                recipient=self.user
            )
            txn.save()


class LedgerEntryModelTests(TestCase):
    """Test suite for LedgerEntry model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            phone_number='+2348012345678',
            password='testpass123'
        )
        
        self.wallet = WalletService.create_wallet_for_user(self.user)
        
        self.txn = Transaction.objects.create(
            user=self.user,
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal('1000.00'),
            reference=generate_transaction_reference()
        )
    
    def test_ledger_entry_creation(self):
        """Test creating a ledger entry."""
        entry = LedgerEntry.objects.create(
            transaction=self.txn,
            wallet=self.wallet,
            entry_type=EntryType.CREDIT,
            amount=Decimal('1000.00'),
            balance_before=Decimal('0.00'),
            balance_after=Decimal('1000.00')
        )
        
        self.assertIsNotNone(entry.id)
        self.assertEqual(entry.transaction, self.txn)
        self.assertEqual(entry.wallet, self.wallet)
        self.assertEqual(entry.entry_type, EntryType.CREDIT)
    
    def test_ledger_entry_immutable(self):
        """Test that ledger entries cannot be updated."""
        entry = LedgerEntry.objects.create(
            transaction=self.txn,
            wallet=self.wallet,
            entry_type=EntryType.CREDIT,
            amount=Decimal('1000.00'),
            balance_before=Decimal('0.00'),
            balance_after=Decimal('1000.00')
        )
        
        # Attempting to update should raise error
        with self.assertRaises(ValidationError):
            entry.amount = Decimal('2000.00')
            entry.save()
    
    def test_balance_calculation_credit(self):
        """Test balance calculation for credit entry."""
        entry = LedgerEntry(
            transaction=self.txn,
            wallet=self.wallet,
            entry_type=EntryType.CREDIT,
            amount=Decimal('1000.00'),
            balance_before=Decimal('500.00'),
            balance_after=Decimal('1500.00')
        )
        
        # Should not raise error
        entry.clean()
    
    def test_balance_calculation_debit(self):
        """Test balance calculation for debit entry."""
        entry = LedgerEntry(
            transaction=self.txn,
            wallet=self.wallet,
            entry_type=EntryType.DEBIT,
            amount=Decimal('300.00'),
            balance_before=Decimal('1000.00'),
            balance_after=Decimal('700.00')
        )
        
        # Should not raise error
        entry.clean()


class LedgerServiceTests(TestCase):
    """Test suite for LedgerService."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='sender@example.com',
            phone_number='+2348012345678',
            password='testpass123'
        )
        
        self.recipient = User.objects.create_user(
            email='recipient@example.com',
            phone_number='+2348012345679',
            password='testpass123'
        )
        
        self.sender_wallet = WalletService.create_wallet_for_user(self.user)
        self.recipient_wallet = WalletService.create_wallet_for_user(self.recipient)
        
        # Give sender some balance
        self.sender_wallet.balance = Decimal('10000.00')
        self.sender_wallet.save()
    
    def test_create_transaction(self):
        """Test creating a transaction."""
        txn = LedgerService.create_transaction(
            user=self.user,
            transaction_type=TransactionType.TRANSFER,
            amount=Decimal('1000.00'),
            recipient=self.recipient,
            description='Test transfer'
        )
        
        self.assertIsNotNone(txn)
        self.assertEqual(txn.user, self.user)
        self.assertEqual(txn.recipient, self.recipient)
        self.assertEqual(txn.amount, Decimal('1000.00'))
        self.assertEqual(txn.status, TransactionStatus.PENDING)
    
    def test_process_debit(self):
        """Test processing a debit."""
        txn = LedgerService.create_transaction(
            user=self.user,
            transaction_type=TransactionType.WITHDRAWAL,
            amount=Decimal('500.00')
        )
        
        initial_balance = self.sender_wallet.balance
        
        entry = LedgerService.process_debit(
            txn=txn,
            wallet=self.sender_wallet,
            amount=Decimal('500.00')
        )
        
        self.sender_wallet.refresh_from_db()
        
        self.assertEqual(entry.entry_type, EntryType.DEBIT)
        self.assertEqual(entry.amount, Decimal('500.00'))
        self.assertEqual(self.sender_wallet.balance, initial_balance - Decimal('500.00'))
    
    def test_process_credit(self):
        """Test processing a credit."""
        txn = LedgerService.create_transaction(
            user=self.recipient,
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal('1000.00')
        )
        
        initial_balance = self.recipient_wallet.balance
        
        entry = LedgerService.process_credit(
            txn=txn,
            wallet=self.recipient_wallet,
            amount=Decimal('1000.00')
        )
        
        self.recipient_wallet.refresh_from_db()
        
        self.assertEqual(entry.entry_type, EntryType.CREDIT)
        self.assertEqual(entry.amount, Decimal('1000.00'))
        self.assertEqual(self.recipient_wallet.balance, initial_balance + Decimal('1000.00'))
    
    def test_insufficient_balance(self):
        """Test that debit fails with insufficient balance."""
        # Empty the wallet
        self.sender_wallet.balance = Decimal('100.00')
        self.sender_wallet.save()
        
        txn = LedgerService.create_transaction(
            user=self.user,
            transaction_type=TransactionType.WITHDRAWAL,
            amount=Decimal('500.00')
        )
        
        with self.assertRaises(ValidationError):
            LedgerService.process_debit(
                txn=txn,
                wallet=self.sender_wallet,
                amount=Decimal('500.00')
            )
    
    def test_frozen_wallet_cannot_debit(self):
        """Test that frozen wallet cannot be debited."""
        self.sender_wallet.is_frozen = True
        self.sender_wallet.save()
        
        txn = LedgerService.create_transaction(
            user=self.user,
            transaction_type=TransactionType.WITHDRAWAL,
            amount=Decimal('500.00')
        )
        
        with self.assertRaises(ValidationError):
            LedgerService.process_debit(
                txn=txn,
                wallet=self.sender_wallet,
                amount=Decimal('500.00')
            )
    
    def test_idempotency(self):
        """Test idempotency key prevents duplicates."""
        idempotency_key = generate_idempotency_key(
            user_id=str(self.user.id),
            transaction_type=TransactionType.TRANSFER,
            amount='1000.00',
            recipient_id=str(self.recipient.id)
        )
        
        # Create first transaction
        txn1 = LedgerService.create_transaction(
            user=self.user,
            transaction_type=TransactionType.TRANSFER,
            amount=Decimal('1000.00'),
            recipient=self.recipient,
            idempotency_key=idempotency_key
        )
        
        # Try to create duplicate
        txn2 = LedgerService.create_transaction(
            user=self.user,
            transaction_type=TransactionType.TRANSFER,
            amount=Decimal('1000.00'),
            recipient=self.recipient,
            idempotency_key=idempotency_key
        )
        
        # Should return the same transaction
        self.assertEqual(txn1.id, txn2.id)
    
    def test_complete_transaction(self):
        """Test completing a transaction."""
        txn = LedgerService.create_transaction(
            user=self.user,
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal('1000.00')
        )
        
        completed_txn = LedgerService.complete_transaction(txn)
        
        self.assertEqual(completed_txn.status, TransactionStatus.COMPLETED)
        self.assertIsNotNone(completed_txn.completed_at)
    
    def test_reverse_transaction(self):
        """Test reversing a completed transaction."""
        # Create and complete a transaction
        txn = LedgerService.create_transaction(
            user=self.user,
            transaction_type=TransactionType.WITHDRAWAL,
            amount=Decimal('500.00')
        )
        
        # Debit wallet
        LedgerService.process_debit(
            txn=txn,
            wallet=self.sender_wallet,
            amount=Decimal('500.00')
        )
        
        # Complete transaction
        LedgerService.complete_transaction(txn)
        
        initial_balance = self.sender_wallet.balance
        
        # Reverse transaction
        admin_user = User.objects.create_superuser(
            email='admin@example.com',
            phone_number='+2348012345680',
            password='adminpass'
        )
        
        reversal_txn = LedgerService.reverse_transaction(
            original_txn=txn,
            reversed_by_user=admin_user,
            reason='Test reversal'
        )
        
        self.sender_wallet.refresh_from_db()
        txn.refresh_from_db()
        
        # Check reversal transaction
        self.assertEqual(reversal_txn.transaction_type, TransactionType.REVERSAL)
        self.assertEqual(reversal_txn.status, TransactionStatus.COMPLETED)
        
        # Check original transaction marked as reversed
        self.assertEqual(txn.status, TransactionStatus.REVERSED)
        self.assertEqual(txn.reversed_by, reversal_txn)
        
        # Check balance restored
        self.assertEqual(self.sender_wallet.balance, initial_balance + Decimal('500.00'))
    
    def test_verify_ledger_balance(self):
        """Test ledger balance verification."""
        txn = LedgerService.create_transaction(
            user=self.user,
            transaction_type=TransactionType.TRANSFER,
            amount=Decimal('1000.00'),
            recipient=self.recipient
        )
        
        # Create balanced entries
        LedgerService.process_debit(
            txn=txn,
            wallet=self.sender_wallet,
            amount=Decimal('1000.00')
        )
        
        LedgerService.process_credit(
            txn=txn,
            wallet=self.recipient_wallet,
            amount=Decimal('1000.00')
        )
        
        # Verify balance
        is_balanced = LedgerService.verify_ledger_balance(txn)
        self.assertTrue(is_balanced)


class TransactionAPITests(APITestCase):
    """Test suite for Transaction API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            email='user@example.com',
            phone_number='+2348012345678',
            password='testpass123'
        )
        
        self.wallet = WalletService.create_wallet_for_user(self.user)
        
        # Create some test transactions
        for i in range(5):
            txn = LedgerService.create_transaction(
                user=self.user,
                transaction_type=TransactionType.DEPOSIT,
                amount=Decimal(f'{(i+1)*100}.00'),
                description=f'Test deposit {i+1}'
            )
            LedgerService.complete_transaction(txn)
    
    def test_list_transactions_authenticated(self):
        """Test listing transactions as authenticated user."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/transactions/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertEqual(len(response.data['data']), 5)
    
    def test_list_transactions_unauthenticated(self):
        """Test that unauthenticated request is rejected."""
        response = self.client.get('/api/transactions/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_filter_by_type(self):
        """Test filtering transactions by type."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/transactions/?type=DEPOSIT')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 5)
    
    def test_get_transaction_detail(self):
        """Test retrieving transaction details."""
        self.client.force_authenticate(user=self.user)
        
        txn = Transaction.objects.filter(user=self.user).first()
        
        response = self.client.get(f'/api/transactions/{txn.id}/')
        
        self.assertEqual(response.status.HTTP_200_OK)
        self.assertEqual(response.data['data']['reference'], txn.reference)
    
    def test_get_transaction_stats(self):
        """Test getting transaction statistics."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/transactions/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_transactions', response.data['data'])
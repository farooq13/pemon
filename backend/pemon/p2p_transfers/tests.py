from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from wallets.services import WalletService
from transactions.models import Transaction, TransactionStatus
from transactions.services import LedgerService

User = get_user_model()


class P2PTransferAPITests(APITestCase):
    """Test suite for P2P Transfer API."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create sender
        self.sender = User.objects.create_user(
            email='sender@example.com',
            phone_number='+2348012345678',
            password='testpass123'
        )
        
        # Create recipient
        self.recipient = User.objects.create_user(
            email='recipient@example.com',
            phone_number='+2348012345679',
            password='testpass123'
        )
        
        # Create wallets
        self.sender_wallet = WalletService.create_wallet_for_user(self.sender)
        self.recipient_wallet = WalletService.create_wallet_for_user(self.recipient)
        
        # Give sender some balance
        self.sender_wallet.balance = Decimal('10000.00')
        self.sender_wallet.save()
    
    def test_successful_transfer(self):
        """Test successful P2P transfer."""
        self.client.force_authenticate(user=self.sender)
        
        initial_sender_balance = self.sender_wallet.balance
        initial_recipient_balance = self.recipient_wallet.balance
        
        transfer_amount = Decimal('1000.00')
        
        response = self.client.post('/api/transfers/p2p/', {
            'recipient_identifier': 'recipient@example.com',
            'amount': '1000.00',
            'description': 'Test transfer'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('data', response.data)
        
        # Verify balances updated
        self.sender_wallet.refresh_from_db()
        self.recipient_wallet.refresh_from_db()
        
        self.assertEqual(
            self.sender_wallet.balance,
            initial_sender_balance - transfer_amount
        )
        self.assertEqual(
            self.recipient_wallet.balance,
            initial_recipient_balance + transfer_amount
        )
        
        # Verify transaction created
        txn_ref = response.data['data']['reference']
        txn = Transaction.objects.get(reference=txn_ref)
        
        self.assertEqual(txn.status, TransactionStatus.COMPLETED)
        self.assertEqual(txn.user, self.sender)
        self.assertEqual(txn.recipient, self.recipient)
        self.assertEqual(txn.amount, transfer_amount)
    
    def test_transfer_by_phone_number(self):
        """Test transfer using phone number."""
        self.client.force_authenticate(user=self.sender)
        
        response = self.client.post('/api/transfers/p2p/', {
            'recipient_identifier': '+2348012345679',
            'amount': '500.00',
            'description': 'Transfer by phone'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_insufficient_balance(self):
        """Test transfer with insufficient balance."""
        self.client.force_authenticate(user=self.sender)
        
        # Try to send more than balance
        response = self.client.post('/api/transfers/p2p/', {
            'recipient_identifier': 'recipient@example.com',
            'amount': '20000.00',  # More than 10000 balance
            'description': 'Too much'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient balance', str(response.data))
    
    def test_invalid_recipient(self):
        """Test transfer to non-existent recipient."""
        self.client.force_authenticate(user=self.sender)
        
        response = self.client.post('/api/transfers/p2p/', {
            'recipient_identifier': 'nonexistent@example.com',
            'amount': '100.00'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('No user found', str(response.data))
    
    def test_transfer_to_self(self):
        """Test that user cannot transfer to themselves."""
        self.client.force_authenticate(user=self.sender)
        
        response = self.client.post('/api/transfers/p2p/', {
            'recipient_identifier': 'sender@example.com',
            'amount': '100.00'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cannot transfer money to yourself', str(response.data))
    
    def test_frozen_wallet_cannot_send(self):
        """Test that frozen wallet cannot send money."""
        # Freeze sender wallet
        self.sender_wallet.is_frozen = True
        self.sender_wallet.save()
        
        self.client.force_authenticate(user=self.sender)
        
        response = self.client.post('/api/transfers/p2p/', {
            'recipient_identifier': 'recipient@example.com',
            'amount': '100.00'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('frozen', str(response.data))
    
    def test_minimum_amount_validation(self):
        """Test minimum transfer amount."""
        self.client.force_authenticate(user=self.sender)
        
        response = self.client.post('/api/transfers/p2p/', {
            'recipient_identifier': 'recipient@example.com',
            'amount': '5.00'  # Below minimum of 10
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Minimum transfer amount', str(response.data))
    
    def test_negative_amount_validation(self):
        """Test negative amount is rejected."""
        self.client.force_authenticate(user=self.sender)
        
        response = self.client.post('/api/transfers/p2p/', {
            'recipient_identifier': 'recipient@example.com',
            'amount': '-100.00'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_unauthenticated_request(self):
        """Test that unauthenticated request is rejected."""
        response = self.client.post('/api/transfers/p2p/', {
            'recipient_identifier': 'recipient@example.com',
            'amount': '100.00'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_idempotency(self):
        """Test that duplicate requests return same transaction."""
        self.client.force_authenticate(user=self.sender)
        
        data = {
            'recipient_identifier': 'recipient@example.com',
            'amount': '1000.00',
            'description': 'Test idempotency'
        }
        
        # First request
        response1 = self.client.post('/api/transfers/p2p/', data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Get balances after first transfer
        self.sender_wallet.refresh_from_db()
        balance_after_first = self.sender_wallet.balance
        
        # Duplicate request (same amount, recipient within 1 minute)
        response2 = self.client.post('/api/transfers/p2p/', data, format='json')
        
        # Should return same transaction
        self.assertEqual(
            response1.data['data']['reference'],
            response2.data['data']['reference']
        )
        
        # Balance should not change again
        self.sender_wallet.refresh_from_db()
        self.assertEqual(self.sender_wallet.balance, balance_after_first)
    
    def test_validate_recipient_endpoint(self):
        """Test recipient validation endpoint."""
        self.client.force_authenticate(user=self.sender)
        
        # Valid recipient
        response = self.client.post('/api/transfers/validate-recipient/', {
            'identifier': 'recipient@example.com'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valid'])
        self.assertIn('data', response.data)
        
        # Invalid recipient
        response = self.client.post('/api/transfers/validate-recipient/', {
            'identifier': 'nonexistent@example.com'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['valid'])
    
    def test_get_recent_recipients(self):
        """Test getting recent recipients."""
        self.client.force_authenticate(user=self.sender)
        
        # Make a transfer first
        LedgerService.create_transaction(
            user=self.sender,
            transaction_type='TRANSFER',
            amount=Decimal('100.00'),
            recipient=self.recipient
        )
        
        response = self.client.get('/api/transfers/recent-recipients/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
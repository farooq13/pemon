from django.test import TestCase
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from wallets.models import Wallet
from wallets.services import WalletService, create_wallet_on_kyc_approval
from kyc.models import KYC

User = get_user_model()


class WalletServiceTests(TestCase):
    """Test suite for WalletService."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            phone_number='+2348012345678',
            password='testpass123'
        )
    
    def test_generate_virtual_account_number(self):
        """Test virtual account number generation."""
        account_number = WalletService.generate_virtual_account_number()
        
        # Should be 10 digits
        self.assertEqual(len(account_number), 10)
        
        # Should start with prefix "20"
        self.assertTrue(account_number.startswith('20'))
        
        # Should be all digits
        self.assertTrue(account_number.isdigit())
    
    def test_virtual_account_uniqueness(self):
        """Test that generated account numbers are unique."""
        # Generate multiple account numbers
        account_numbers = set()
        for _ in range(100):
            account_number = WalletService.generate_virtual_account_number()
            account_numbers.add(account_number)
        
        # All should be unique
        self.assertEqual(len(account_numbers), 100)
    
    def test_create_wallet_for_user(self):
        """Test wallet creation for a user."""
        wallet = WalletService.create_wallet_for_user(self.user)
        
        # Wallet should be created
        self.assertIsNotNone(wallet)
        self.assertEqual(wallet.user, self.user)
        
        # Balance should be 0
        self.assertEqual(wallet.balance, Decimal('0.00'))
        
        # Virtual account should be generated
        self.assertIsNotNone(wallet.virtual_account_number)
        self.assertEqual(len(wallet.virtual_account_number), 10)
        
        # Should not be frozen by default
        self.assertFalse(wallet.is_frozen)
    
    def test_create_duplicate_wallet_raises_error(self):
        """Test that creating duplicate wallet raises ValidationError."""
        # Create first wallet
        WalletService.create_wallet_for_user(self.user)
        
        # Attempting to create second wallet should raise error
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            WalletService.create_wallet_for_user(self.user)
    
    def test_get_user_wallet(self):
        """Test retrieving user's wallet."""
        # Initially should return None
        wallet = WalletService.get_user_wallet(self.user)
        self.assertIsNone(wallet)
        
        # Create wallet
        created_wallet = WalletService.create_wallet_for_user(self.user)
        
        # Should now return the wallet
        retrieved_wallet = WalletService.get_user_wallet(self.user)
        self.assertEqual(retrieved_wallet, created_wallet)
    
    def test_freeze_wallet(self):
        """Test freezing a wallet."""
        wallet = WalletService.create_wallet_for_user(self.user)
        
        # Freeze wallet
        reason = "Suspicious activity"
        frozen_wallet = WalletService.freeze_wallet(wallet, reason)
        
        self.assertTrue(frozen_wallet.is_frozen)
        self.assertEqual(frozen_wallet.freeze_reason, reason)
    
    def test_unfreeze_wallet(self):
        """Test unfreezing a wallet."""
        wallet = WalletService.create_wallet_for_user(self.user)
        
        # Freeze then unfreeze
        WalletService.freeze_wallet(wallet, "Test freeze")
        unfrozen_wallet = WalletService.unfreeze_wallet(wallet)
        
        self.assertFalse(unfrozen_wallet.is_frozen)
        self.assertEqual(unfrozen_wallet.freeze_reason, "")
    
    def test_is_wallet_active(self):
        """Test wallet active status check."""
        wallet = WalletService.create_wallet_for_user(self.user)
        
        # Initially active
        self.assertTrue(WalletService.is_wallet_active(wallet))
        
        # Freeze wallet
        WalletService.freeze_wallet(wallet)
        self.assertFalse(WalletService.is_wallet_active(wallet))
        
        # Unfreeze
        WalletService.unfreeze_wallet(wallet)
        self.assertTrue(WalletService.is_wallet_active(wallet))


class WalletSignalTests(TestCase):
    """Test suite for wallet creation signals."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='kyc@example.com',
            phone_number='+2348012345679',
            password='testpass123'
        )
    
    def test_wallet_created_on_kyc_approval(self):
        """Test that wallet is auto-created when KYC is approved."""
        # Create KYC record
        kyc = KYC.objects.create(
            user=self.user,
            bvn='12345678901',
            date_of_birth='1990-01-01',
            address='123 Test St',
            city='Lagos',
            state='Lagos',
            id_type='passport',
            id_number='A12345678',
            tier=1,
            status='pending'
        )
        
        # User should not have wallet yet
        self.assertFalse(Wallet.objects.filter(user=self.user).exists())
        
        # Approve KYC
        kyc.status = 'approved'
        kyc.save()
        
        # Wallet should now be created
        self.assertTrue(Wallet.objects.filter(user=self.user).exists())
        
        wallet = Wallet.objects.get(user=self.user)
        self.assertEqual(wallet.balance, Decimal('0.00'))
        self.assertFalse(wallet.is_frozen)


class WalletAPITests(APITestCase):
    """Test suite for Wallet API endpoints."""
    
    def setUp(self):
        """Set up test data and authentication."""
        self.client = APIClient()
        
        # Create regular user
        self.user = User.objects.create_user(
            email='user@example.com',
            phone_number='+2348012345680',
            password='testpass123'
        )
        
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            phone_number='+2348012345681',
            password='adminpass123'
        )
        
        # Create wallet for regular user
        self.wallet = WalletService.create_wallet_for_user(self.user)
    
    def test_get_wallet_balance_authenticated(self):
        """Test retrieving wallet balance as authenticated user."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/wallet/balance/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('data', response.data)
        self.assertEqual(
            response.data['data']['virtual_account_number'],
            self.wallet.virtual_account_number
        )
    
    def test_get_wallet_balance_unauthenticated(self):
        """Test that unauthenticated request is rejected."""
        response = self.client.get('/api/wallet/balance/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_wallet_balance_no_wallet(self):
        """Test retrieving balance for user without wallet."""
        user_no_wallet = User.objects.create_user(
            email='nowallet@example.com',
            phone_number='+2348012345682',
            password='testpass123'
        )
        
        self.client.force_authenticate(user=user_no_wallet)
        response = self.client.get('/api/wallet/balance/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['status'], 'error')
        self.assertIn('WALLET_NOT_FOUND', response.data['error_code'])
    
    def test_get_wallet_detail(self):
        """Test retrieving detailed wallet information."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/wallet/detail/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('kyc_tier', response.data['data'])
        self.assertIn('kyc_limits', response.data['data'])
    
    def test_freeze_wallet_as_admin(self):
        """Test freezing wallet as admin."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {'reason': 'Test freeze'}
        response = self.client.post(
            f'/api/wallet/{self.wallet.id}/freeze/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        
        # Verify wallet is frozen
        self.wallet.refresh_from_db()
        self.assertTrue(self.wallet.is_frozen)
    
    def test_freeze_wallet_as_regular_user(self):
        """Test that regular user cannot freeze wallets."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(
            f'/api/wallet/{self.wallet.id}/freeze/',
            {'reason': 'Test'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_unfreeze_wallet_as_admin(self):
        """Test unfreezing wallet as admin."""
        # First freeze the wallet
        WalletService.freeze_wallet(self.wallet, "Test freeze")
        
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.post(
            f'/api/wallet/{self.wallet.id}/unfreeze/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        
        # Verify wallet is unfrozen
        self.wallet.refresh_from_db()
        self.assertFalse(self.wallet.is_frozen)
    
    def test_check_wallet_status(self):
        """Test checking wallet status."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/wallet/status/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['data']['has_wallet'])
        self.assertTrue(response.data['data']['is_active'])
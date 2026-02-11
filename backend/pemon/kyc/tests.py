from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .models import KYC
from .services import KYCService
from .tier_limits import TIER_LIMITS

User = get_user_model()


class KYCModelTest(TestCase):
    """Tests for KYC model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='aish@example.com',
            phone_number='+2348012345678',
            first_name='Aisha',
            last_name='Sulaiman',
            password='TestPass123!'
        )

    def test_create_kyc(self):
        """Test creating a KYC record."""
        kyc = KYC.objects.create(
            user=self.user,
            bvn='12345678901',
            date_of_birth=date(1990, 1, 1),
            address='123 Main Street',
            city='Gombe',
            state='Gombe',
        )
        
        self.assertEqual(kyc.user, self.user)
        self.assertEqual(kyc.tier, 0)
        self.assertEqual(kyc.status, KYC.Status.PENDING)
        self.assertEqual(kyc.bvn, '12345678901')

    def test_kyc_str_method(self):
        """Test KYC string representation."""
        kyc = KYC.objects.create(user=self.user)
        expected = f"{self.user.email} - Tier 0 (Pending Review)"
        self.assertEqual(str(kyc), expected)

    def test_get_tier_limits(self):
        """Test getting tier limits."""
        kyc = KYC.objects.create(user=self.user, tier=1)
        limits = kyc.get_tier_limits()
        
        self.assertEqual(limits['daily_limit'], TIER_LIMITS[1]['daily_limit'])
        self.assertEqual(limits['single_transaction_limit'], TIER_LIMITS[1]['single_transaction_limit'])

    def test_can_transact(self):
        """Test transaction eligibility check."""
        kyc = KYC.objects.create(
            user=self.user,
            tier=1,
            status=KYC.Status.APPROVED
        )
        
        # Within limit
        can_transact, reason = kyc.can_transact(Decimal('5000'))
        self.assertTrue(can_transact)
        self.assertEqual(reason, '')
        
        # Exceeds single transaction limit
        can_transact, reason = kyc.can_transact(Decimal('15000'))
        self.assertFalse(can_transact)
        self.assertIn('exceeds single transaction limit', reason)

    def test_approve_kyc(self):
        """Test KYC approval."""
        admin = User.objects.create_superuser(
            email='admin@example.com',
            phone_number='+2348087654321',
            first_name='Admin',
            last_name='User',
            password='AdminPass123!'
        )
        
        kyc = KYC.objects.create(user=self.user)
        kyc.approve(verified_by=admin, tier=1)
        
        self.assertEqual(kyc.status, KYC.Status.APPROVED)
        self.assertEqual(kyc.tier, 1)
        self.assertEqual(kyc.verified_by, admin)
        self.assertIsNotNone(kyc.verified_at)

    def test_reject_kyc(self):
        """Test KYC rejection."""
        admin = User.objects.create_superuser(
            email='admin@example.com',
            phone_number='+2348087654321',
            first_name='Admin',
            last_name='User',
            password='AdminPass123!'
        )
        
        kyc = KYC.objects.create(user=self.user)
        reason = 'Invalid documents'
        kyc.reject(verified_by=admin, reason=reason)
        
        self.assertEqual(kyc.status, KYC.Status.REJECTED)
        self.assertEqual(kyc.rejection_reason, reason)
        self.assertEqual(kyc.verified_by, admin)
        self.assertIsNotNone(kyc.verified_at)


class KYCServiceTest(TestCase):
    """Tests for KYC service layer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            phone_number='+2348012345678',
            first_name='John',
            last_name='Doe',
            password='TestPass123!'
        )

    def test_get_or_create_kyc(self):
        """Test getting or creating KYC."""
        kyc, created = KYCService.get_or_create_kyc(self.user)
        
        self.assertTrue(created)
        self.assertEqual(kyc.user, self.user)
        
        # Get existing
        kyc2, created2 = KYCService.get_or_create_kyc(self.user)
        self.assertFalse(created2)
        self.assertEqual(kyc.id, kyc2.id)

    def test_validate_bvn(self):
        """Test BVN validation."""
        # Valid BVN
        is_valid, error = KYCService.validate_bvn('12345678901')
        self.assertTrue(is_valid)
        
        # Invalid - too short
        is_valid, error = KYCService.validate_bvn('123456789')
        self.assertFalse(is_valid)
        
        # Invalid - contains letters
        is_valid, error = KYCService.validate_bvn('1234567890A')
        self.assertFalse(is_valid)

    def test_validate_nin(self):
        """Test NIN validation."""
        # Valid NIN
        is_valid, error = KYCService.validate_nin('12345678901')
        self.assertTrue(is_valid)
        
        # Empty (allowed)
        is_valid, error = KYCService.validate_nin('')
        self.assertTrue(is_valid)
        
        # Invalid format
        is_valid, error = KYCService.validate_nin('123')
        self.assertFalse(is_valid)


class KYCSubmissionAPITest(APITestCase):
    """Tests for KYC submission API."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            phone_number='+2348012345678',
            first_name='John',
            last_name='Doe',
            password='TestPass123!'
        )
        self.submit_url = reverse('kyc:submit')

    def create_test_image(self):
        """Create a test image file."""
        file = BytesIO()
        image = Image.new('RGB', (100, 100), color='red')
        image.save(file, 'JPEG')
        file.seek(0)
        return SimpleUploadedFile(
            'test.jpg',
            file.read(),
            content_type='image/jpeg'
        )

    def test_submit_kyc_success(self):
        """Test successful KYC submission."""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'bvn': '12345678901',
            'date_of_birth': '1990-01-01',
            'address': '123 Main Street',
            'city': 'Lagos',
            'state': 'Lagos',
            'id_type': 'NIN',
            'id_number': '12345678901',
            'id_document': self.create_test_image(),
            'selfie': self.create_test_image(),
        }
        
        response = self.client.post(self.submit_url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('kyc', response.data)
        
        # Verify KYC was created
        kyc = KYC.objects.get(user=self.user)
        self.assertEqual(kyc.bvn, '12345678901')
        self.assertEqual(kyc.status, KYC.Status.PENDING)

    def test_submit_kyc_without_authentication(self):
        """Test KYC submission without authentication."""
        response = self.client.post(self.submit_url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_submit_kyc_invalid_bvn(self):
        """Test KYC submission with invalid BVN."""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'bvn': '123',  # Invalid BVN
            'date_of_birth': '1990-01-01',
            'address': '123 Main Street',
            'city': 'Lagos',
            'state': 'Lagos',
            'id_type': 'NIN',
            'id_number': '12345678901',
            'id_document': self.create_test_image(),
            'selfie': self.create_test_image(),
        }
        
        response = self.client.post(self.submit_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_kyc_missing_documents(self):
        """Test KYC submission without required documents."""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'bvn': '12345678901',
            'date_of_birth': '1990-01-01',
            'address': '123 Main Street',
            'city': 'Lagos',
            'state': 'Lagos',
        }
        
        response = self.client.post(self.submit_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class KYCStatusAPITest(APITestCase):
    """Tests for KYC status API."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            phone_number='+2348012345678',
            first_name='John',
            last_name='Doe',
            password='TestPass123!'
        )
        self.status_url = reverse('kyc:status')

    def test_get_kyc_status_no_kyc(self):
        """Test getting KYC status when no KYC exists."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(self.status_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['tier'], 0)
        self.assertEqual(response.data['status'], KYC.Status.PENDING)

    def test_get_kyc_status_with_kyc(self):
        """Test getting KYC status with existing KYC."""
        self.client.force_authenticate(user=self.user)
        
        # Create approved KYC
        admin = User.objects.create_superuser(
            email='admin@example.com',
            phone_number='+2348087654321',
            first_name='Admin',
            last_name='User',
            password='AdminPass123!'
        )
        
        kyc = KYC.objects.create(user=self.user)
        kyc.approve(verified_by=admin, tier=1)
        
        response = self.client.get(self.status_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['tier'], 1)
        self.assertEqual(response.data['status'], KYC.Status.APPROVED)
        self.assertIn('limits', response.data)
        self.assertIn('features', response.data)

    def test_get_kyc_status_unauthenticated(self):
        """Test getting KYC status without authentication."""
        response = self.client.get(self.status_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TransactionEligibilityAPITest(APITestCase):
    """Tests for transaction eligibility check API."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            phone_number='+2348012345678',
            first_name='John',
            last_name='Doe',
            password='TestPass123!'
        )
        self.check_url = reverse('kyc:check-eligibility')

    def test_check_eligibility_no_kyc(self):
        """Test eligibility check without KYC."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(self.check_url, {'amount': 5000})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['can_transact'])
        self.assertIn('KYC verification required', response.data['reason'])

    def test_check_eligibility_approved_kyc(self):
        """Test eligibility check with approved KYC."""
        self.client.force_authenticate(user=self.user)
        
        # Create approved KYC
        admin = User.objects.create_superuser(
            email='admin@example.com',
            phone_number='+2348087654321',
            first_name='Admin',
            last_name='User',
            password='AdminPass123!'
        )
        
        kyc = KYC.objects.create(user=self.user)
        kyc.approve(verified_by=admin, tier=1)
        
        # Check amount within limit
        response = self.client.post(self.check_url, {'amount': 5000})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['can_transact'])
        
        # Check amount exceeding limit
        response = self.client.post(self.check_url, {'amount': 15000})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['can_transact'])
        self.assertIn('exceeds', response.data['reason'])

    def test_check_eligibility_invalid_amount(self):
        """Test eligibility check with invalid amount."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(self.check_url, {'amount': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response = self.client.post(self.check_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
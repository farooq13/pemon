
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .models import OTPVerification

User = get_user_model()


class UserModelTest(TestCase):
    """Tests for the User model."""

    def setUp(self):
        """Set up test data."""
        self.user_data = {
            'email': 'test@example.com',
            'phone_number': '+2348012345678',
            'first_name': 'John',
            'last_name': 'Doe',
            'password': 'TestPass123!',
        }

    def test_create_user(self):
        """Test creating a new user."""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.email, self.user_data['email'])
        self.assertEqual(user.phone_number, self.user_data['phone_number'])
        self.assertTrue(user.check_password(self.user_data['password']))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.email_verified)
        self.assertFalse(user.phone_verified)

    def test_create_user_without_email(self):
        """Test creating user without email raises error."""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email='',
                phone_number=self.user_data['phone_number'],
                password=self.user_data['password']
            )

    def test_create_user_without_phone(self):
        """Test creating user without phone raises error."""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email=self.user_data['email'],
                phone_number='',
                password=self.user_data['password']
            )

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(**self.user_data)
        
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)
        self.assertTrue(user.email_verified)
        self.assertTrue(user.phone_verified)

    def test_user_str_method(self):
        """Test user string representation."""
        user = User.objects.create_user(**self.user_data)
        expected_str = f"{user.email} (John Doe)"
        self.assertEqual(str(user), expected_str)

    def test_get_full_name(self):
        """Test get_full_name method."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_full_name(), 'John Doe')

    def test_get_short_name(self):
        """Test get_short_name method."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_short_name(), 'John')

    def test_verify_email(self):
        """Test email verification."""
        user = User.objects.create_user(**self.user_data)
        self.assertFalse(user.email_verified)
        
        user.verify_email()
        user.refresh_from_db()
        
        self.assertTrue(user.email_verified)
        self.assertIsNotNone(user.email_verified_at)

    def test_verify_phone(self):
        """Test phone verification."""
        user = User.objects.create_user(**self.user_data)
        self.assertFalse(user.phone_verified)
        
        user.verify_phone()
        user.refresh_from_db()
        
        self.assertTrue(user.phone_verified)
        self.assertIsNotNone(user.phone_verified_at)

    def test_is_verified(self):
        """Test is_verified method."""
        user = User.objects.create_user(**self.user_data)
        self.assertFalse(user.is_verified())
        
        user.verify_email()
        self.assertTrue(user.is_verified())

    def test_is_fully_verified(self):
        """Test is_fully_verified method."""
        user = User.objects.create_user(**self.user_data)
        self.assertFalse(user.is_fully_verified())
        
        user.verify_email()
        self.assertFalse(user.is_fully_verified())
        
        user.verify_phone()
        self.assertTrue(user.is_fully_verified())


class UserRegistrationAPITest(APITestCase):
    """Tests for user registration API."""

    def setUp(self):
        """Set up test client and URLs."""
        self.client = APIClient()
        self.register_url = reverse('accounts:register')
        self.valid_user_data = {
            'email': 'newuser@example.com',
            'phone_number': '+2348012345678',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
        }

    def test_register_user_success(self):
        """Test successful user registration."""
        response = self.client.post(
            self.register_url,
            self.valid_user_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('message', response.data)
        
        # Verify user was created
        self.assertTrue(
            User.objects.filter(email=self.valid_user_data['email']).exists()
        )
        
        # Verify OTP was created
        user = User.objects.get(email=self.valid_user_data['email'])
        self.assertTrue(
            OTPVerification.objects.filter(
                user=user,
                otp_type=OTPVerification.OTPType.EMAIL
            ).exists()
        )

    def test_register_duplicate_email(self):
        """Test registration with duplicate email."""
        # Create first user
        User.objects.create_user(
            email=self.valid_user_data['email'],
            phone_number='+2348087654321',
            first_name='John',
            last_name='Doe',
            password='Password123!'
        )
        
        # Try to register with same email
        response = self.client.post(
            self.register_url,
            self.valid_user_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_phone(self):
        """Test registration with duplicate phone number."""
        # Create first user
        User.objects.create_user(
            email='other@example.com',
            phone_number=self.valid_user_data['phone_number'],
            first_name='John',
            last_name='Doe',
            password='Password123!'
        )
        
        # Try to register with same phone
        response = self.client.post(
            self.register_url,
            self.valid_user_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_mismatch(self):
        """Test registration with non-matching passwords."""
        data = self.valid_user_data.copy()
        data['password_confirm'] = 'DifferentPass123!'
        
        response = self.client.post(
            self.register_url,
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_weak_password(self):
        """Test registration with weak password."""
        data = self.valid_user_data.copy()
        data['password'] = '12345678'
        data['password_confirm'] = '12345678'
        
        response = self.client.post(
            self.register_url,
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_invalid_phone_format(self):
        """Test registration with invalid phone format."""
        data = self.valid_user_data.copy()
        data['phone_number'] = '12345'  # Invalid format
        
        response = self.client.post(
            self.register_url,
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_required_fields(self):
        """Test registration with missing required fields."""
        response = self.client.post(
            self.register_url,
            {'email': 'test@example.com'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLoginAPITest(APITestCase):
    """Tests for user login API."""

    def setUp(self):
        """Set up test client, user, and URLs."""
        self.client = APIClient()
        self.login_url = reverse('accounts:login')
        
        self.user_data = {
            'email': 'testuser@example.com',
            'phone_number': '+2348012345678',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'TestPass123!',
        }
        
        self.user = User.objects.create_user(**self.user_data)

    def test_login_success(self):
        """Test successful user login."""
        response = self.client.post(
            self.login_url,
            {
                'email': self.user_data['email'],
                'password': self.user_data['password'],
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = self.client.post(
            self.login_url,
            {
                'email': self.user_data['email'],
                'password': 'WrongPassword123!',
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_inactive_user(self):
        """Test login with inactive user."""
        self.user.is_active = False
        self.user.save()
        
        response = self.client.post(
            self.login_url,
            {
                'email': self.user_data['email'],
                'password': self.user_data['password'],
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user(self):
        """Test login with non-existent user."""
        response = self.client.post(
            self.login_url,
            {
                'email': 'nonexistent@example.com',
                'password': 'SomePass123!',
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class OTPVerificationTest(APITestCase):
    """Tests for OTP verification."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.verify_url = reverse('accounts:verify-otp')
        
        self.user = User.objects.create_user(
            email='test@example.com',
            phone_number='+2348012345678',
            first_name='Test',
            last_name='User',
            password='TestPass123!'
        )
        
        self.otp = OTPVerification.objects.create(
            user=self.user,
            otp_type=OTPVerification.OTPType.EMAIL,
            otp_code='123456',
            expires_at=timezone.now() + timedelta(minutes=10)
        )

    def test_verify_otp_success(self):
        """Test successful OTP verification."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(
            self.verify_url,
            {
                'otp_code': '123456',
                'otp_type': 'EMAIL',
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check user is verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

    def test_verify_invalid_otp(self):
        """Test verification with invalid OTP."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(
            self.verify_url,
            {
                'otp_code': '999999',
                'otp_type': 'EMAIL',
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_expired_otp(self):
        """Test verification with expired OTP."""
        # Make OTP expired
        self.otp.expires_at = timezone.now() - timedelta(minutes=1)
        self.otp.save()
        
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(
            self.verify_url,
            {
                'otp_code': '123456',
                'otp_type': 'EMAIL',
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_used_otp(self):
        """Test verification with already used OTP."""
        self.otp.mark_as_used()
        
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(
            self.verify_url,
            {
                'otp_code': '123456',
                'otp_type': 'EMAIL',
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_unauthenticated(self):
        """Test OTP verification without authentication."""
        response = self.client.post(
            self.verify_url,
            {
                'otp_code': '123456',
                'otp_type': 'EMAIL',
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PasswordChangeTest(APITestCase):
    """Tests for password change functionality."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.change_password_url = reverse('accounts:change-password')
        
        self.user = User.objects.create_user(
            email='test@example.com',
            phone_number='+2348012345678',
            first_name='Test',
            last_name='User',
            password='OldPass123!'
        )

    def test_change_password_success(self):
        """Test successful password change."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(
            self.change_password_url,
            {
                'old_password': 'OldPass123!',
                'new_password': 'NewPass123!',
                'new_password_confirm': 'NewPass123!',
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass123!'))

    def test_change_password_wrong_old_password(self):
        """Test password change with wrong old password."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(
            self.change_password_url,
            {
                'old_password': 'WrongPass123!',
                'new_password': 'NewPass123!',
                'new_password_confirm': 'NewPass123!',
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_mismatch(self):
        """Test password change with non-matching new passwords."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(
            self.change_password_url,
            {
                'old_password': 'OldPass123!',
                'new_password': 'NewPass123!',
                'new_password_confirm': 'DifferentPass123!',
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
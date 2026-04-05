import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from core.models import TimeStampedModel


class UserManager(BaseUserManager):
    """
    Custom user manager for Pemon User model.
    
    Handles user creation with email as the unique identifier instead of username.
    """

    def create_user(self, email, phone_number, password=None, **extra_fields):
        """
        Create and save a regular user with the given email, phone, and password.

        """
        if not email:
            raise ValueError('Users must have an email address')
        if not phone_number:
            raise ValueError('Users must have a phone number')

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            phone_number=phone_number,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, phone_number, password=None, **extra_fields):
        """
        Create and save a superuser with the given email, phone, and password.          
        Returns:
            User: Created superuser instance
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('email_verified', True)
        extra_fields.setdefault('phone_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """    
    Uses email as the unique identifier instead of username.
    Includes phone number verification and role management.

    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
        db_index=True,
        help_text='User\'s email address (used for login)'
    )
    
    phone_regex = RegexValidator(
        regex=r'^\+?234?\d{10,13}$',
        message="Phone number must be in format: '+2348012345678' or '08012345678'"
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        unique=True,
        db_index=True,
        help_text='User\'s phone number in Nigerian format'
    )
    
    first_name = models.CharField(
        max_length=150,
        help_text='User\'s first name'
    )
    
    last_name = models.CharField(
        max_length=150,
        help_text='User\'s last name'
    )
    
    # Account Status
    is_active = models.BooleanField(
        default=True,
        help_text='Designates whether this user should be treated as active. '
                  'Unselect this instead of deleting accounts.'
    )
    
    is_staff = models.BooleanField(
        default=False,
        help_text='Designates whether the user can log into the admin site.'
    )
    
    # User Roles
    is_merchant = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Designates whether the user is a merchant'
    )
    
    is_agent = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Designates whether the user is an agent'
    )
    
    # Verification Status
    email_verified = models.BooleanField(
        default=False,
        help_text='Whether the user has verified their email address'
    )
    
    phone_verified = models.BooleanField(
        default=False,
        help_text='Whether the user has verified their phone number'
    )
    
    email_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when email was verified'
    )
    
    phone_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when phone was verified'
    )
    
    # Timestamps
    date_joined = models.DateTimeField(
        default=timezone.now,
        help_text='Date when the user joined'
    )
    
    last_login = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last login timestamp'
    )
    
    # Profile Image
    profile_image = models.ImageField(
        upload_to='profile_images/',
        null=True,
        blank=True,
        help_text='User\'s profile image'
    )
    
    # Transfer PIN
    transfer_pin = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text='Hashed 4-digit transfer PIN'
    )
    
    # Device Information (for security)
    last_login_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of last login'
    )
    
    last_login_device = models.CharField(
        max_length=255,
        blank=True,
        help_text='Device information of last login'
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone_number', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email', 'is_active']),
            models.Index(fields=['phone_number', 'is_active']),
            models.Index(fields=['is_merchant', 'is_active']),
            models.Index(fields=['is_agent', 'is_active']),
        ]

    def __str__(self):
        return f"{self.email} ({self.get_full_name()})"

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        
        Returns:
            str: User's full name
        """
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.email

    def get_short_name(self):
        """
        Return the short name for the user (first name).
        
        Returns:
            str: User's first name
        """
        return self.first_name or self.email.split('@')[0]

    def verify_email(self):
        """Mark email as verified and save timestamp."""
        self.email_verified = True
        self.email_verified_at = timezone.now()
        self.save(update_fields=['email_verified', 'email_verified_at', 'updated_at'])

    def verify_phone(self):
        """Mark phone as verified and save timestamp."""
        self.phone_verified = True
        self.phone_verified_at = timezone.now()
        self.save(update_fields=['phone_verified', 'phone_verified_at', 'updated_at'])

    def is_verified(self):
        """
        Check if user has completed basic verification (email OR phone).
        
        Returns:
            bool: True if either email or phone is verified
        """
        return self.email_verified or self.phone_verified

    def is_fully_verified(self):
        """
        Check if user has completed full verification (email AND phone).
        
        Returns:
            bool: True if both email and phone are verified
        """
        return self.email_verified and self.phone_verified

    @property
    def has_transfer_pin(self):
        """Check if user has set a transfer PIN."""
        return bool(self.transfer_pin)

    def set_transfer_pin(self, raw_pin):
        """
        Hash and set the transfer PIN.
        Must be precisely 4 digits.
        """
        from django.contrib.auth.hashers import make_password
        self.transfer_pin = make_password(raw_pin)
        self.save(update_fields=['transfer_pin', 'updated_at'])

    def check_transfer_pin(self, raw_pin):
        """
        Check if the provided PIN matches the hashed transfer PIN.
        """
        if not self.has_transfer_pin:
            return False
            
        from django.contrib.auth.hashers import check_password
        return check_password(raw_pin, self.transfer_pin)



class OTPVerification(TimeStampedModel):
    """
    Model for storing OTP (One-Time Password) for email/phone verification.
    
    OTPs expire after a certain period and can only be used once.
    """
    
    class OTPType(models.TextChoices):
        EMAIL = 'EMAIL', 'Email Verification'
        PHONE = 'PHONE', 'Phone Verification'
        PASSWORD_RESET = 'PASSWORD_RESET', 'Password Reset'
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='otp_codes',
        help_text='User this OTP belongs to'
    )
    
    otp_type = models.CharField(
        max_length=20,
        choices=OTPType.choices,
        help_text='Type of OTP verification'
    )
    
    otp_code = models.CharField(
        max_length=6,
        help_text='6-digit OTP code'
    )
    
    is_used = models.BooleanField(
        default=False,
        help_text='Whether this OTP has been used'
    )
    
    expires_at = models.DateTimeField(
        help_text='When this OTP expires'
    )

    class Meta:
        verbose_name = 'OTP Verification'
        verbose_name_plural = 'OTP Verifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'otp_type', 'is_used']),
            models.Index(fields=['otp_code', 'expires_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.otp_type} - {self.otp_code}"

    def is_valid(self):
        """
        Check if OTP is still valid (not used and not expired).
        
        Returns:
            bool: True if OTP is valid
        """
        return not self.is_used and timezone.now() < self.expires_at

    def mark_as_used(self):
        """Mark this OTP as used."""
        self.is_used = True
        self.save(update_fields=['is_used', 'updated_at'])
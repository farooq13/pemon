from datetime import timedelta

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from core.utils import normalize_phone_number, validate_nigerian_phone
from .models import OTPVerification, User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    
    Validates user input, creates new user account, and returns JWT tokens.
    
    """
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='Password must be at least 8 characters'
    )
    
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='Re-enter your password'
    )
    
    # Read-only fields returned after registration
    access_token = serializers.SerializerMethodField(read_only=True)
    refresh_token = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'phone_number',
            'first_name',
            'last_name',
            'password',
            'password_confirm',
            'access_token',
            'refresh_token',
        ]
        read_only_fields = ['id']

    def validate_email(self, value):
        # Normalize email (lowercase)
        value = value.lower().strip()
        
        # Check if email already exists
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'A user with this email address already exists.'
            )
        
        return value

    def validate_phone_number(self, value):
        # Validate format
        is_valid, error_message = validate_nigerian_phone(value)
        if not is_valid:
            raise serializers.ValidationError(error_message)
        
        # Normalize phone number
        normalized = normalize_phone_number(value)
        
        # Check if phone number already exists
        if User.objects.filter(phone_number=normalized).exists():
            raise serializers.ValidationError(
                'A user with this phone number already exists.'
            )
        
        return normalized

    def validate_password(self, value):
        """
        Validate password strength using Django's validators.
        
        Raises:
            serializers.ValidationError: If password is weak
        """
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        
        return value

    def validate(self, attrs):
        """
        Validate that passwords match.

        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        
        return attrs

    def create(self, validated_data):
        """
        Create new user account and generate OTP for verification.
        
        """
        # Remove password_confirm as it's not needed
        validated_data.pop('password_confirm', None)
        
        # Extract password
        password = validated_data.pop('password')
        
        # Create user
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        # Generate OTP for email verification
        from core.utils import generate_otp
        otp_code = generate_otp(6)
        
        OTPVerification.objects.create(
            user=user,
            otp_type=OTPVerification.OTPType.EMAIL,
            otp_code=otp_code,
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        # Send verification email (async task)
        from core.tasks import send_email_task
        send_email_task.delay(
            subject='Verify Your Pemon Account',
            message=f'Your verification code is: {otp_code}',
            recipient_list=[user.email],
        )
        
        return user

    def get_access_token(self, obj):
        """Get JWT access token for the user."""
        refresh = RefreshToken.for_user(obj)
        return str(refresh.access_token)

    def get_refresh_token(self, obj):
        """Get JWT refresh token for the user."""
        refresh = RefreshToken.for_user(obj)
        return str(refresh)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer with additional user information.
    
    Returns user details along with tokens for better client-side state management.
    """
    
    def validate(self, attrs):
        """
        Validate credentials and return tokens with user data.
            
        Raises:
            serializers.ValidationError: If credentials are invalid
        """
        data = super().validate(attrs)
        
        # Add user information to response
        data['user'] = UserProfileSerializer(self.user).data
        
        # Update last login info
        self.user.last_login = timezone.now()
        self.user.save(update_fields=['last_login'])
        
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.
    
    Used for displaying user details in responses.
    """
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    is_verified = serializers.BooleanField(source='is_verified', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'phone_number',
            'first_name',
            'last_name',
            'full_name',
            'is_active',
            'is_merchant',
            'is_agent',
            'email_verified',
            'phone_verified',
            'is_verified',
            'profile_image',
            'date_joined',
        ]
        read_only_fields = fields


class OTPVerificationSerializer(serializers.Serializer):
    """
    Serializer for OTP verification.
    
    Validates OTP code and marks email/phone as verified.
    """
    
    otp_code = serializers.CharField(
        max_length=6,
        min_length=6,
        help_text='6-digit OTP code'
    )
    
    otp_type = serializers.ChoiceField(
        choices=OTPVerification.OTPType.choices,
        help_text='Type of OTP (EMAIL or PHONE)'
    )

    def validate(self, attrs):
        """
        Validate OTP code.
                
        Returns:
            dict: Validated attributes
            
        Raises:
            serializers.ValidationError: If OTP is invalid or expired
        """
        user = self.context['request'].user
        otp_code = attrs['otp_code']
        otp_type = attrs['otp_type']
        
        # Find valid OTP
        try:
            otp = OTPVerification.objects.get(
                user=user,
                otp_code=otp_code,
                otp_type=otp_type,
                is_used=False,
                expires_at__gt=timezone.now()
            )
        except OTPVerification.DoesNotExist:
            raise serializers.ValidationError({
                'otp_code': 'Invalid or expired OTP code.'
            })
        
        attrs['otp_instance'] = otp
        return attrs

    def save(self):
        """
        Mark OTP as used and verify email/phone.
        
        Returns:
            User: Updated user instance
        """
        otp = self.validated_data['otp_instance']
        user = otp.user
        
        # Mark OTP as used
        otp.mark_as_used()
        
        # Verify email or phone based on OTP type
        if otp.otp_type == OTPVerification.OTPType.EMAIL:
            user.verify_email()
        elif otp.otp_type == OTPVerification.OTPType.PHONE:
            user.verify_phone()
        
        return user


class ResendOTPSerializer(serializers.Serializer):
    """
    Serializer for resending OTP.
    
    Generates new OTP and sends it via email or SMS.
    """
    
    otp_type = serializers.ChoiceField(
        choices=OTPVerification.OTPType.choices,
        help_text='Type of OTP to resend (EMAIL or PHONE)'
    )

    def save(self):
        """
        Generate and send new OTP.
        
        Returns:
            OTPVerification: Created OTP instance
        """
        user = self.context['request'].user
        otp_type = self.validated_data['otp_type']
        
        # Generate new OTP
        from core.utils import generate_otp
        otp_code = generate_otp(6)
        
        # Create OTP record
        otp = OTPVerification.objects.create(
            user=user,
            otp_type=otp_type,
            otp_code=otp_code,
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        # Send OTP based on type
        if otp_type == OTPVerification.OTPType.EMAIL:
            from core.tasks import send_email_task
            send_email_task.delay(
                subject='Verify Your Pemon Account',
                message=f'Your verification code is: {otp_code}',
                recipient_list=[user.email],
            )
        elif otp_type == OTPVerification.OTPType.PHONE:
            from core.tasks import send_sms_task
            send_sms_task.delay(
                phone_number=user.phone_number,
                message=f'Your Pemon verification code is: {otp_code}',
            )
        
        return otp


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for password change.
    
    Requires current password for verification.
    """
    
    old_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    new_password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    def validate_old_password(self, value):
        """Validate that old password is correct."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value

    def validate_new_password(self, value):
        """Validate new password strength."""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        """Validate that new passwords match."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Passwords do not match.'
            })
        return attrs

    def save(self):
        """Update user password."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import (
    CustomTokenObtainPairSerializer,
    OTPVerificationSerializer,
    PasswordChangeSerializer,
    ResendOTPSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
)

User = get_user_model()


@extend_schema_view(
    post=extend_schema(
        summary="Register new user",
        description="Create a new user account with email and phone number. "
                    "Returns JWT tokens for immediate authentication.",
        tags=['Authentication'],
    )
)
class UserRegistrationView(generics.CreateAPIView):
    """
    Creates a new user account and returns JWT access and refresh tokens.
    Also generates and sends OTP for email verification.
    
    """
    
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """
        Handle user registration request.
        
        Creates user, generates tokens, and sends verification OTP.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        headers = self.get_success_headers(serializer.data)
        
        return Response(
            {
                'message': 'Registration successful! Please check your email for verification code.',
                'user': serializer.data,
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )


@extend_schema_view(
    post=extend_schema(
        summary="Login user",
        description="Authenticate user and return JWT access and refresh tokens.",
        tags=['Authentication'],
    )
)
class CustomTokenObtainPairView(TokenObtainPairView):
    """    
    Authenticates user credentials and returns JWT tokens along with user profile.
  
    """
    
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema_view(
    post=extend_schema(
        summary="Refresh access token",
        description="Get a new access token using refresh token.",
        tags=['Authentication'],
    )
)
class CustomTokenRefreshView(TokenRefreshView):
    """
    Uses refresh token to generate new access token.
    
    """
    pass


@extend_schema_view(
    get=extend_schema(
        summary="Get user profile",
        description="Retrieve authenticated user's profile information.",
        tags=['User Profile'],
    ),
    put=extend_schema(
        summary="Update user profile",
        description="Update authenticated user's profile information.",
        tags=['User Profile'],
    ),
    patch=extend_schema(
        summary="Partial update user profile",
        description="Partially update authenticated user's profile information.",
        tags=['User Profile'],
    ),
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Return the authenticated user."""
        return self.request.user


@extend_schema_view(
    post=extend_schema(
        summary="Verify OTP",
        description="Verify email or phone number using OTP code.",
        tags=['Verification'],
    )
)
class OTPVerificationView(APIView):
    """
    Verify email or phone using 6-digit OTP code.
    
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = OTPVerificationSerializer

    def post(self, request):
        """Handle OTP verification request."""
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        verification_type = serializer.validated_data['otp_type']
        message = f"{'Email' if verification_type == 'EMAIL' else 'Phone'} verified successfully!"
        
        return Response(
            {
                'message': message,
                'user': UserProfileSerializer(user).data,
            },
            status=status.HTTP_200_OK
        )


@extend_schema_view(
    post=extend_schema(
        summary="Resend OTP",
        description="Request a new OTP code for email or phone verification.",
        tags=['Verification'],
    )
)
class ResendOTPView(APIView):
    """
    Generate and send new OTP code.
    
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = ResendOTPSerializer

    def post(self, request):
        """Handle OTP resend request."""
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        otp = serializer.save()
        
        otp_type = serializer.validated_data['otp_type']
        destination = 'email' if otp_type == 'EMAIL' else 'phone'
        
        return Response(
            {
                'message': f'OTP sent successfully to your {destination}.',
                'expires_in_minutes': 10,
            },
            status=status.HTTP_200_OK
        )


@extend_schema_view(
    post=extend_schema(
        summary="Change password",
        description="Change user password (requires current password).",
        tags=['User Profile'],
    )
)
class PasswordChangeView(APIView):
    """
    Change user password with current password verification.
  
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    def post(self, request):
        """Handle password change request."""
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            {
                'message': 'Password changed successfully.',
            },
            status=status.HTTP_200_OK
        )


@extend_schema_view(
    post=extend_schema(
        summary="Logout user",
        description="Logout user by blacklisting refresh token.",
        tags=['Authentication'],
    )
)
class LogoutView(APIView):
    """
    Blacklist the refresh token to prevent further use.
    
    """
    
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Handle logout request."""
        try:
            from rest_framework_simplejwt.tokens import RefreshToken
            
            refresh_token = request.data.get('refresh_token')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {'message': 'Logged out successfully.'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': 'Invalid token.'},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(
    summary="Check authentication status",
    description="Check if current user is authenticated.",
    tags=['Authentication'],
)
class AuthStatusView(APIView):
    """
    Returns current user info if authenticated.
    
    """
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return authentication status and user info."""
        return Response(
            {
                'authenticated': True,
                'user': UserProfileSerializer(request.user).data,
            },
            status=status.HTTP_200_OK
        )
from django.urls import path

from .views import (
    AuthStatusView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    LogoutView,
    OTPVerificationView,
    PasswordChangeView,
    ResendOTPView,
    UserProfileView,
    UserRegistrationView,
)

app_name = 'accounts'

urlpatterns = [
    # Authentication endpoints
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token-refresh'),
    path('status/', AuthStatusView.as_view(), name='auth-status'),
    
    # User profile
    path('profile/', UserProfileView.as_view(), name='profile'),
    
    # OTP verification
    path('verify-otp/', OTPVerificationView.as_view(), name='verify-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    
    # Password management
    path('change-password/', PasswordChangeView.as_view(), name='change-password'),
   
]
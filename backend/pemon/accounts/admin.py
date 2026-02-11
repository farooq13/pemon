from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import OTPVerification, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin interface for User model."""
    
    list_display = [
        'email',
        'get_full_name',
        'phone_number',
        'verification_status',
        'role_badges',
        'is_active',
        'date_joined',
    ]
    
    list_filter = [
        'is_active',
        'is_staff',
        'is_merchant',
        'is_agent',
        'email_verified',
        'phone_verified',
        'date_joined',
    ]
    
    search_fields = [
        'email',
        'phone_number',
        'first_name',
        'last_name',
    ]
    
    readonly_fields = [
        'id',
        'date_joined',
        'last_login',
        'email_verified_at',
        'phone_verified_at',
        'created_at',
        'updated_at',
    ]
    
    ordering = ['-date_joined']
    
    fieldsets = (
        ('Personal Information', {
            'fields': (
                'id',
                'email',
                'phone_number',
                'first_name',
                'last_name',
                'profile_image',
            )
        }),
        ('Permissions & Roles', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'is_merchant',
                'is_agent',
                'groups',
                'user_permissions',
            )
        }),
        ('Verification Status', {
            'fields': (
                'email_verified',
                'email_verified_at',
                'phone_verified',
                'phone_verified_at',
            )
        }),
        ('Security & Login Info', {
            'fields': (
                'password',
                'last_login',
                'last_login_ip',
                'last_login_device',
            )
        }),
        ('Important Dates', {
            'fields': (
                'date_joined',
                'created_at',
                'updated_at',
            )
        }),
    )
    
    add_fieldsets = (
        ('Create New User', {
            'classes': ('wide',),
            'fields': (
                'email',
                'phone_number',
                'first_name',
                'last_name',
                'password1',
                'password2',
                'is_active',
                'is_staff',
            ),
        }),
    )
    
    def verification_status(self, obj):
        """Display verification status with colored badges."""
        email_status = 'Email Verified' if obj.email_verified else 'Email Not Verified'
        phone_status = 'Phone Verified' if obj.phone_verified else 'Phone Not Verified'
        
        email_color = '#28a745' if obj.email_verified else '#dc3545'
        phone_color = '#28a745' if obj.phone_verified else '#dc3545'
        
        return format_html(
            '<span style="color: {};">{}</span> | '
            '<span style="color: {};">{}</span>',
            email_color, email_status,
            phone_color, phone_status
        )
    verification_status.short_description = 'Verification'
    
    def role_badges(self, obj):
        """Display user roles as badges."""
        badges = []
        
        if obj.is_superuser:
            badges.append('<span style="background: #dc3545; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">ADMIN</span>')
        if obj.is_merchant:
            badges.append('<span style="background: #007bff; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">MERCHANT</span>')
        if obj.is_agent:
            badges.append('<span style="background: #ffc107; color: black; padding: 3px 8px; border-radius: 3px; font-size: 11px;">AGENT</span>')
        
        if not badges:
            badges.append('<span style="background: #6c757d; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">USER</span>')
        
        return format_html(' '.join(badges))
    role_badges.short_description = 'Roles'
    
    def get_full_name(self, obj):
        """Display user's full name."""
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'first_name'


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    """Admin interface for OTP verification."""
    
    list_display = [
        'id',
        'user_email',
        'otp_type',
        'otp_code',
        'status_badge',
        'expires_at',
        'created_at',
    ]
    
    list_filter = [
        'otp_type',
        'is_used',
        'created_at',
        'expires_at',
    ]
    
    search_fields = [
        'user__email',
        'user__phone_number',
        'otp_code',
    ]
    
    readonly_fields = [
        'id',
        'user',
        'otp_type',
        'otp_code',
        'is_used',
        'expires_at',
        'created_at',
        'updated_at',
    ]
    
    date_hierarchy = 'created_at'
    
    ordering = ['-created_at']
    
    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def status_badge(self, obj):
        """Display OTP status with colored badge."""
        if obj.is_used:
            status = 'USED'
            color = '#6c757d'
        elif obj.is_valid():
            status = 'VALID'
            color = '#28a745'
        else:
            status = 'EXPIRED'
            color = '#dc3545'
        
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, status
        )
    status_badge.short_description = 'Status'
    
    def has_add_permission(self, request):
        """Disable adding OTP through admin (should be generated by system)."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing OTP through admin."""
        return False
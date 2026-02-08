from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Wallet
from .services import WalletService


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    """
    Admin interface for Wallet model.
    
    Provides comprehensive wallet management capabilities including
    search, filtering, and inline actions for freeze/unfreeze.
    """
    
    list_display = [
        'id',
        'user_email',
        'virtual_account_number',
        'formatted_balance',
        'status_badge',
        'created_at',
        'freeze_actions',
    ]
    
    list_filter = [
        'is_frozen',
        'created_at',
        'updated_at',
    ]
    
    search_fields = [
        'user__email',
        'user__phone_number',
        'virtual_account_number',
        'id',
    ]
    
    readonly_fields = [
        'id',
        'virtual_account_number',
        'created_at',
        'updated_at',
        'user_link',
        'transaction_count',
    ]
    
    fieldsets = (
        ('Wallet Information', {
            'fields': (
                'id',
                'user_link',
                'virtual_account_number',
                'balance',
            )
        }),
        ('Status', {
            'fields': (
                'is_frozen',
                'freeze_reason',
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at',
                'transaction_count',
            ),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['freeze_selected_wallets', 'unfreeze_selected_wallets']
    
    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    def formatted_balance(self, obj):
        """Display formatted balance with currency symbol."""
        return format_html(
            '<strong>₦{:,.2f}</strong>',
            obj.balance
        )
    formatted_balance.short_description = 'Balance'
    formatted_balance.admin_order_field = 'balance'
    
    def status_badge(self, obj):
        """Display wallet status with colored badge."""
        if obj.is_frozen:
            return format_html(
                '<span style="background-color: #dc3545; color: white; '
                'padding: 3px 10px; border-radius: 3px; font-weight: bold;">'
                'FROZEN</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #28a745; color: white; '
                'padding: 3px 10px; border-radius: 3px; font-weight: bold;">'
                'ACTIVE</span>'
            )
    status_badge.short_description = 'Status'
    
    def user_link(self, obj):
        """Display link to user in admin."""
        if obj.user:
            url = reverse('admin:accounts_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'
    user_link.short_description = 'User'
    
    def transaction_count(self, obj):
        """Display count of transactions associated with this wallet."""
       
        try:
            count = obj.transactions_sent.count() + obj.transactions_received.count()
            return f"{count} transactions"
        except:
            return "N/A"
    transaction_count.short_description = 'Transactions'
    
    def freeze_actions(self, obj):
        """Display freeze/unfreeze action buttons."""
        if obj.is_frozen:
            return format_html(
                '<a class="button" href="javascript:void(0)" '
                'onclick="if(confirm(\'Unfreeze this wallet?\')) {{ '
                'window.location.href=\'/admin/wallets/wallet/{}/unfreeze/\' }}">'
                'Unfreeze</a>',
                obj.id
            )
        else:
            return format_html(
                '<a class="button" href="javascript:void(0)" '
                'onclick="if(confirm(\'Freeze this wallet?\')) {{ '
                'window.location.href=\'/admin/wallets/wallet/{}/freeze/\' }}">'
                'Freeze</a>',
                obj.id
            )
    freeze_actions.short_description = 'Actions'
    
    def freeze_selected_wallets(self, request, queryset):
        """
        Admin action to freeze selected wallets.
        """
        count = 0
        for wallet in queryset:
            if not wallet.is_frozen:
                WalletService.freeze_wallet(
                    wallet,
                    reason="Frozen by admin via bulk action"
                )
                count += 1
        
        self.message_user(
            request,
            f"Successfully froze {count} wallet(s)."
        )
    freeze_selected_wallets.short_description = "Freeze selected wallets"
    
    def unfreeze_selected_wallets(self, request, queryset):
        """
        Admin action to unfreeze selected wallets.
        """
        count = 0
        for wallet in queryset:
            if wallet.is_frozen:
                WalletService.unfreeze_wallet(wallet)
                count += 1
        
        self.message_user(
            request,
            f"Successfully unfroze {count} wallet(s)."
        )
    unfreeze_selected_wallets.short_description = "Unfreeze selected wallets"
    
    def has_delete_permission(self, request, obj=None):
        """
        Prevent deletion of wallets from admin.
        
        Wallets should never be deleted as they contain transaction history.
        """
        return False
    
    def get_queryset(self, request):
        """
        Optimize queryset with select_related.
        """
        queryset = super().get_queryset(request)
        return queryset.select_related('user')
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum
from decimal import Decimal

from .models import Transaction, LedgerEntry, TransactionStatus


class LedgerEntryInline(admin.TabularInline):
    """
    Inline display of ledger entries within transaction admin.
    """
    model = LedgerEntry
    extra = 0
    can_delete = False
    
    fields = [
        'entry_type',
        'wallet_link',
        'amount',
        'balance_before',
        'balance_after',
        'created_at',
    ]
    
    readonly_fields = fields
    
    def wallet_link(self, obj):
        """Display link to wallet."""
        if obj.wallet:
            url = reverse('admin:wallets_wallet_change', args=[obj.wallet.id])
            return format_html(
                '<a href="{}">{}</a>',
                url,
                obj.wallet.user.email
            )
        return '-'
    wallet_link.short_description = 'Wallet'
    
    def has_add_permission(self, request, obj=None):
        """Prevent adding ledger entries manually."""
        return False


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """
    Admin interface for Transaction model.
    
    Provides comprehensive transaction viewing with proper
    immutability enforcement and audit trail display.
    """
    
    list_display = [
        'reference',
        'user_email',
        'transaction_type',
        'formatted_amount',
        'status_badge',
        'recipient_email',
        'created_at',
        'reversal_status',
    ]
    
    list_filter = [
        'status',
        'transaction_type',
        'created_at',
    ]
    
    search_fields = [
        'reference',
        'user__email',
        'recipient__email',
        'idempotency_key',
        'description',
    ]
    
    readonly_fields = [
        'id',
        'reference',
        'user_link',
        'recipient_link',
        'reversed_by_link',
        'original_transaction_link',
        'created_at',
        'updated_at',
        'completed_at',
        'ledger_balance_check',
    ]
    
    fieldsets = (
        ('Transaction Information', {
            'fields': (
                'id',
                'reference',
                'transaction_type',
                'amount',
                'status',
                'idempotency_key',
            )
        }),
        ('Parties', {
            'fields': (
                'user_link',
                'recipient_link',
            )
        }),
        ('Description & Metadata', {
            'fields': (
                'description',
                'metadata',
            )
        }),
        ('Reversal Information', {
            'fields': (
                'reversed_by_link',
                'original_transaction_link',
            ),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
                'completed_at',
            ),
            'classes': ('collapse',),
        }),
        ('Audit', {
            'fields': (
                'ledger_balance_check',
            ),
            'classes': ('collapse',),
        }),
    )
    
    inlines = [LedgerEntryInline]
    
    actions = ['mark_as_failed']
    
    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def recipient_email(self, obj):
        """Display recipient email."""
        if obj.recipient:
            return obj.recipient.email
        return '-'
    recipient_email.short_description = 'Recipient'
    recipient_email.admin_order_field = 'recipient__email'
    
    def formatted_amount(self, obj):
        """Display formatted amount."""
        return format_html(
            '<strong>₦{:,.2f}</strong>',
            obj.amount
        )
    formatted_amount.short_description = 'Amount'
    formatted_amount.admin_order_field = 'amount'
    
    def status_badge(self, obj):
        """Display status with colored badge."""
        colors = {
            TransactionStatus.PENDING: '#ffc107',
            TransactionStatus.PROCESSING: '#17a2b8',
            TransactionStatus.COMPLETED: '#28a745',
            TransactionStatus.FAILED: '#dc3545',
            TransactionStatus.REVERSED: '#6c757d',
        }
        
        color = colors.get(obj.status, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 3px; font-weight: bold;">'
            '{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def reversal_status(self, obj):
        """Display reversal status."""
        if obj.reversed_by:
            return format_html(
                '<span style="color: red;">✗ Reversed</span>'
            )
        elif obj.original_transaction:
            return format_html(
                '<span style="color: blue;">↺ Reversal</span>'
            )
        return '-'
    reversal_status.short_description = 'Reversal'
    
    def user_link(self, obj):
        """Display link to user."""
        if obj.user:
            url = reverse('admin:accounts_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'
    user_link.short_description = 'User'
    
    def recipient_link(self, obj):
        """Display link to recipient."""
        if obj.recipient:
            url = reverse('admin:accounts_user_change', args=[obj.recipient.id])
            return format_html('<a href="{}">{}</a>', url, obj.recipient.email)
        return '-'
    recipient_link.short_description = 'Recipient'
    
    def reversed_by_link(self, obj):
        """Display link to reversal transaction."""
        if obj.reversed_by:
            url = reverse('admin:transactions_transaction_change', args=[obj.reversed_by.id])
            return format_html(
                '<a href="{}">{}</a>',
                url,
                obj.reversed_by.reference
            )
        return '-'
    reversed_by_link.short_description = 'Reversed By'
    
    def original_transaction_link(self, obj):
        """Display link to original transaction."""
        if obj.original_transaction:
            url = reverse('admin:transactions_transaction_change', args=[obj.original_transaction.id])
            return format_html(
                '<a href="{}">{}</a>',
                url,
                obj.original_transaction.reference
            )
        return '-'
    original_transaction_link.short_description = 'Original Transaction'
    
    def ledger_balance_check(self, obj):
        """
        Verify double-entry bookkeeping integrity.
        
        Sum of debits should equal sum of credits.
        """
        entries = obj.ledger_entries.all()
        
        if not entries.exists():
            return format_html(
                '<span style="color: orange;">⚠ No ledger entries</span>'
            )
        
        total_debits = entries.filter(
            entry_type='DEBIT'
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        total_credits = entries.filter(
            entry_type='CREDIT'
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        if abs(total_debits - total_credits) < Decimal('0.01'):
            return format_html(
                '<span style="color: green;">✓ Balanced (₦{:,.2f} = ₦{:,.2f})</span>',
                total_debits,
                total_credits
            )
        else:
            return format_html(
                '<span style="color: red;">✗ UNBALANCED! Debit: ₦{:,.2f}, Credit: ₦{:,.2f}</span>',
                total_debits,
                total_credits
            )
    ledger_balance_check.short_description = 'Ledger Balance Check'
    
    def mark_as_failed(self, request, queryset):
        """
        Admin action to mark pending transactions as failed.
        
        Only affects pending transactions.
        """
        updated = queryset.filter(
            status=TransactionStatus.PENDING
        ).update(
            status=TransactionStatus.FAILED
        )
        
        self.message_user(
            request,
            f"Marked {updated} transaction(s) as failed."
        )
    mark_as_failed.short_description = "Mark selected as FAILED"
    
    def has_delete_permission(self, request, obj=None):
        """
        Prevent deletion of transactions.
        
        Transactions must remain for audit trail.
        Use reversals instead of deletions.
        """
        return False
    
    def has_change_permission(self, request, obj=None):
        """
        Prevent editing of completed transactions.
        
        Only allow changing pending/failed transactions.
        """
        if obj and obj.status in [
            TransactionStatus.COMPLETED,
            TransactionStatus.REVERSED
        ]:
            return False
        return super().has_change_permission(request, obj)
    
    def get_queryset(self, request):
        """
        Optimize queryset with select_related.
        """
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'user',
            'recipient',
            'reversed_by',
            'original_transaction'
        ).prefetch_related('ledger_entries')


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    """
    Admin interface for LedgerEntry model.
    
    Read-only view of all ledger entries for audit purposes.
    """
    
    list_display = [
        'id',
        'transaction_reference',
        'wallet_user',
        'entry_type',
        'formatted_amount',
        'formatted_balance_before',
        'formatted_balance_after',
        'created_at',
    ]
    
    list_filter = [
        'entry_type',
        'created_at',
    ]
    
    search_fields = [
        'transaction__reference',
        'wallet__user__email',
        'wallet__virtual_account_number',
    ]
    
    readonly_fields = [
        'id',
        'transaction',
        'wallet',
        'entry_type',
        'amount',
        'balance_before',
        'balance_after',
        'description',
        'created_at',
    ]
    
    def transaction_reference(self, obj):
        """Display transaction reference."""
        return obj.transaction.reference
    transaction_reference.short_description = 'Transaction'
    transaction_reference.admin_order_field = 'transaction__reference'
    
    def wallet_user(self, obj):
        """Display wallet owner."""
        return obj.wallet.user.email
    wallet_user.short_description = 'User'
    wallet_user.admin_order_field = 'wallet__user__email'
    
    def formatted_amount(self, obj):
        """Display formatted amount."""
        color = 'red' if obj.entry_type == 'DEBIT' else 'green'
        symbol = '-' if obj.entry_type == 'DEBIT' else '+'
        
        return format_html(
            '<span style="color: {};">{} ₦{:,.2f}</span>',
            color,
            symbol,
            obj.amount
        )
    formatted_amount.short_description = 'Amount'
    
    def formatted_balance_before(self, obj):
        """Display formatted balance before."""
        return f"₦{obj.balance_before:,.2f}"
    formatted_balance_before.short_description = 'Balance Before'
    
    def formatted_balance_after(self, obj):
        """Display formatted balance after."""
        return f"₦{obj.balance_after:,.2f}"
    formatted_balance_after.short_description = 'Balance After'
    
    def has_add_permission(self, request):
        """Prevent manual creation of ledger entries."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of ledger entries."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent editing of ledger entries (immutable)."""
        return False
    
    def get_queryset(self, request):
        """Optimize queryset."""
        queryset = super().get_queryset(request)
        return queryset.select_related('transaction', 'wallet', 'wallet__user')
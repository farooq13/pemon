from django.contrib import admin, messages
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import get_object_or_404, redirect

from .models import Wallet
from .services import WalletService


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):

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

    # ===============================
    # CUSTOM ADMIN URLS (FIX)
    # ===============================

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                '<uuid:wallet_id>/freeze/',
                self.admin_site.admin_view(self.freeze_wallet),
                name='wallet-freeze',
            ),
            path(
                '<uuid:wallet_id>/unfreeze/',
                self.admin_site.admin_view(self.unfreeze_wallet),
                name='wallet-unfreeze',
            ),
        ]

        return custom_urls + urls

    # ===============================
    # DISPLAY METHODS
    # ===============================

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'

    def status_badge(self, obj):
        if obj.is_frozen:
            return format_html(
                '<span style="background:#dc3545;color:white;padding:3px 10px;border-radius:3px;font-weight:bold;">FROZEN</span>'
            )
        return format_html(
            '<span style="background:#28a745;color:white;padding:3px 10px;border-radius:3px;font-weight:bold;">ACTIVE</span>'
        )
    status_badge.short_description = 'Status'

    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_link.short_description = 'User'

    def transaction_count(self, obj):
        try:
            count = obj.transactions_sent.count() + obj.transactions_received.count()
            return f"{count} transactions"
        except Exception:
            return "N/A"
    transaction_count.short_description = 'Transactions'

    # ===============================
    # FREEZE BUTTONS (FIXED)
    # ===============================

    def freeze_actions(self, obj):
        if obj.is_frozen:
            url = reverse('admin:wallet-freeze', args=[obj.id]).replace("freeze", "unfreeze")
            return format_html('<a class="button" href="{}">Unfreeze</a>', url)

        url = reverse('admin:wallet-freeze', args=[obj.id])
        return format_html('<a class="button" href="{}">Freeze</a>', url)

    freeze_actions.short_description = 'Actions'

    # ===============================
    # FREEZE HANDLERS (FIXED)
    # ===============================

    def freeze_wallet(self, request, wallet_id):
        wallet = get_object_or_404(Wallet, id=wallet_id)

        if wallet.is_frozen:
            messages.warning(request, "Wallet already frozen.")
        else:
            WalletService.freeze_wallet(wallet, "Frozen via admin")
            messages.success(request, "Wallet frozen successfully.")

        return redirect(
            reverse('admin:wallets_wallet_change', args=[wallet.id])
        )

    def unfreeze_wallet(self, request, wallet_id):
        wallet = get_object_or_404(Wallet, id=wallet_id)

        if not wallet.is_frozen:
            messages.warning(request, "Wallet is not frozen.")
        else:
            WalletService.unfreeze_wallet(wallet)
            messages.success(request, "Wallet unfrozen successfully.")

        return redirect(
            reverse('admin:wallets_wallet_change', args=[wallet.id])
        )

    # ===============================
    # BULK ACTIONS
    # ===============================

    def freeze_selected_wallets(self, request, queryset):
        count = 0
        for wallet in queryset:
            if not wallet.is_frozen:
                WalletService.freeze_wallet(wallet, "Frozen via bulk admin action")
                count += 1

        self.message_user(request, f"Successfully froze {count} wallet(s).")

    def unfreeze_selected_wallets(self, request, queryset):
        count = 0
        for wallet in queryset:
            if wallet.is_frozen:
                WalletService.unfreeze_wallet(wallet)
                count += 1

        self.message_user(request, f"Successfully unfroze {count} wallet(s).")

    # ===============================
    # SECURITY
    # ===============================

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

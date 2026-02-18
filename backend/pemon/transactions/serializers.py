from rest_framework import serializers
from decimal import Decimal

from .models import Transaction, LedgerEntry, TransactionType, TransactionStatus


class LedgerEntrySerializer(serializers.ModelSerializer):
    """Serializer for ledger entries."""
    
    wallet_account_number = serializers.SerializerMethodField()
    
    class Meta:
        model = LedgerEntry
        fields = [
            'id',
            'wallet',
            'wallet_account_number',
            'entry_type',
            'amount',
            'balance_before',
            'balance_after',
            'description',
            'created_at',
        ]
    
    def get_wallet_account_number(self, obj):
        """Get wallet account number."""
        if obj.wallet and hasattr(obj.wallet, 'virtual_account_number'):
            return obj.wallet.virtual_account_number
        return None


class TransactionSerializer(serializers.ModelSerializer):
    """Transaction serializer with account numbers (no emails)."""
    
    # User details (using account number)
    user_account = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    
    # Recipient details (using account number)
    recipient_account = serializers.SerializerMethodField()
    recipient_name = serializers.SerializerMethodField()
    
    # Status and type displays
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    
    # Formatted values
    formatted_amount = serializers.SerializerMethodField()
    
    # User-specific fields (is this transaction a debit or credit for the current user?)
    is_debit = serializers.SerializerMethodField()
    is_credit = serializers.SerializerMethodField()
    counterparty_name = serializers.SerializerMethodField()
    counterparty_account = serializers.SerializerMethodField()
    
    # Ledger entries
    ledger_entries = LedgerEntrySerializer(many=True, read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'reference',
            'transaction_type',
            'type_display',
            'status',
            'status_display',
            'amount',
            'formatted_amount',
            'description',
            'user_account',
            'user_name',
            'recipient_account',
            'recipient_name',
            'is_debit',
            'is_credit',
            'counterparty_name',
            'counterparty_account',
            'ledger_entries',
            'metadata',
            'created_at',
            'updated_at',
        ]
    
    def get_user_account(self, obj):
        """Get sender account number."""
        if obj.user and hasattr(obj.user, 'wallet'):
            return obj.user.wallet.virtual_account_number
        return None
    
    def get_user_name(self, obj):
        """Get sender full name."""
        if obj.user:
            full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
            return full_name if full_name else "User"
        return None
    
    def get_recipient_account(self, obj):
        """Get recipient account number."""
        if obj.recipient and hasattr(obj.recipient, 'wallet'):
            return obj.recipient.wallet.virtual_account_number
        return None
    
    def get_recipient_name(self, obj):
        """Get recipient full name."""
        if obj.recipient:
            full_name = f"{obj.recipient.first_name} {obj.recipient.last_name}".strip()
            return full_name if full_name else "Recipient"
        return None
    
    def get_formatted_amount(self, obj):
        """Get formatted amount with currency."""
        return f"₦{obj.amount:,.2f}"
    
    def get_is_debit(self, obj):
        """Check if this transaction is a debit for the current user."""
        request = self.context.get('request')
        if not request or not request.user:
            return False
        
        # User is sender = debit
        return obj.user == request.user
    
    def get_is_credit(self, obj):
        """Check if this transaction is a credit for the current user."""
        request = self.context.get('request')
        if not request or not request.user:
            return False
        
        # User is recipient = credit
        return obj.recipient == request.user
    
    def get_counterparty_name(self, obj):
        """Get the other party's name (for display in transaction list)."""
        request = self.context.get('request')
        if not request or not request.user:
            return None
        
        # If current user is sender, show recipient
        if obj.user == request.user:
            if obj.recipient:
                full_name = f"{obj.recipient.first_name} {obj.recipient.last_name}".strip()
                return full_name if full_name else "Recipient"
            return "External"
        
        # If current user is recipient, show sender
        if obj.recipient == request.user:
            full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
            return full_name if full_name else "Sender"
        
        return None
    
    def get_counterparty_account(self, obj):
        """Get the other party's account number."""
        request = self.context.get('request')
        if not request or not request.user:
            return None
        
        # If current user is sender, show recipient account
        if obj.user == request.user:
            if obj.recipient and hasattr(obj.recipient, 'wallet'):
                return obj.recipient.wallet.virtual_account_number
            return None
        
        # If current user is recipient, show sender account
        if obj.recipient == request.user:
            if obj.user and hasattr(obj.user, 'wallet'):
                return obj.user.wallet.virtual_account_number
            return None
        
        return None

class TransactionListSerializer(serializers.ModelSerializer):
    """
    Serializer for transaction list view.
    
    Returns summary information for transactions.
    """
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    recipient_email = serializers.SerializerMethodField()
    formatted_amount = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    is_debit = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'reference',
            'transaction_type',
            'type_display',
            'amount',
            'formatted_amount',
            'status',
            'status_display',
            'user_email',
            'recipient_email',
            'description',
            'is_debit',
            'created_at',
        ]
        read_only_fields = fields
    
    def get_recipient_email(self, obj):
        """Get recipient email if exists."""
        if obj.recipient:
            return obj.recipient.email
        return None
    
    def get_formatted_amount(self, obj):
        """Format amount with currency symbol."""
        return f"₦{obj.amount:,.2f}"
    
    def get_is_debit(self, obj):
        """
        Determine if this transaction debited the user's wallet.
        
        For the current user viewing their transactions.
        """
        user = self.context.get('request').user if self.context.get('request') else None
        
        if not user:
            return None
        
        # Check if any ledger entry for this user's wallet is a debit
        user_entry = obj.ledger_entries.filter(wallet__user=user).first()
        
        if user_entry:
            return user_entry.entry_type == 'DEBIT'
        
        return None


class TransactionDetailSerializer(serializers.ModelSerializer):
    """
    Detailed transaction serializer with ledger entries.
    
    Used for single transaction retrieval.
    """
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    recipient_email = serializers.SerializerMethodField()
    recipient_name = serializers.SerializerMethodField()
    formatted_amount = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    ledger_entries = LedgerEntrySerializer(many=True, read_only=True)
    reversed_by_reference = serializers.SerializerMethodField()
    original_transaction_reference = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'reference',
            'transaction_type',
            'type_display',
            'amount',
            'formatted_amount',
            'status',
            'status_display',
            'user_email',
            'user_name',
            'recipient_email',
            'recipient_name',
            'description',
            'metadata',
            'ledger_entries',
            'reversed_by_reference',
            'original_transaction_reference',
            'created_at',
            'updated_at',
            'completed_at',
        ]
        read_only_fields = fields
    
    def get_user_name(self, obj):
        """Get user's full name."""
        user = obj.user
        if hasattr(user, 'first_name') and hasattr(user, 'last_name'):
            full_name = f"{user.first_name} {user.last_name}".strip()
            return full_name if full_name else user.email
        return user.email
    
    def get_recipient_email(self, obj):
        """Get recipient email if exists."""
        if obj.recipient:
            return obj.recipient.email
        return None
    
    def get_recipient_name(self, obj):
        """Get recipient's full name."""
        if not obj.recipient:
            return None
        
        user = obj.recipient
        if hasattr(user, 'first_name') and hasattr(user, 'last_name'):
            full_name = f"{user.first_name} {user.last_name}".strip()
            return full_name if full_name else user.email
        return user.email
    
    def get_formatted_amount(self, obj):
        """Format amount with currency symbol."""
        return f"₦{obj.amount:,.2f}"
    
    def get_reversed_by_reference(self, obj):
        """Get reversal transaction reference if exists."""
        if obj.reversed_by:
            return obj.reversed_by.reference
        return None
    
    def get_original_transaction_reference(self, obj):
        """Get original transaction reference if this is a reversal."""
        if obj.original_transaction:
            return obj.original_transaction.reference
        return None


class TransactionStatsSerializer(serializers.Serializer):
    """
    Serializer for transaction statistics.
    """
    
    total_transactions = serializers.IntegerField()
    total_debits = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_credits = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_debits_formatted = serializers.CharField()
    total_credits_formatted = serializers.CharField()
    net_flow = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_flow_formatted = serializers.CharField()
    
    # Breakdown by type
    by_type = serializers.DictField()
    
    # Recent activity
    recent_transactions = TransactionListSerializer(many=True, read_only=True)


    """Enhanced transaction serializer with user context."""
    
    # User details
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    
    # Recipient details
    recipient_email = serializers.EmailField(source='recipient.email', read_only=True, allow_null=True)
    recipient_name = serializers.SerializerMethodField()
    
    # Status and type displays
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    
    # Formatted values
    formatted_amount = serializers.SerializerMethodField()
    
    # User-specific fields (is this transaction a debit or credit for the current user?)
    is_debit = serializers.SerializerMethodField()
    is_credit = serializers.SerializerMethodField()
    counterparty_name = serializers.SerializerMethodField()
    counterparty_email = serializers.SerializerMethodField()
    
    # Ledger entries
    ledger_entries = LedgerEntrySerializer(many=True, read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'reference',
            'transaction_type',
            'type_display',
            'status',
            'status_display',
            'amount',
            'formatted_amount',
            'description',
            'user_email',
            'user_name',
            'recipient_email',
            'recipient_name',
            'is_debit',
            'is_credit',
            'counterparty_name',
            'counterparty_email',
            'ledger_entries',
            'metadata',
            'created_at',
            'updated_at',
        ]
    
    def get_user_name(self, obj):
        """Get sender full name."""
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email
        return None
    
    def get_recipient_name(self, obj):
        """Get recipient full name."""
        if obj.recipient:
            return f"{obj.recipient.first_name} {obj.recipient.last_name}".strip() or obj.recipient.email
        return None
    
    def get_formatted_amount(self, obj):
        """Get formatted amount with currency."""
        return f"₦{obj.amount:,.2f}"
    
    def get_is_debit(self, obj):
        """Check if this transaction is a debit for the current user."""
        request = self.context.get('request')
        if not request or not request.user:
            return False
        
        # User is sender = debit
        return obj.user == request.user
    
    def get_is_credit(self, obj):
        """Check if this transaction is a credit for the current user."""
        request = self.context.get('request')
        if not request or not request.user:
            return False
        
        # User is recipient = credit
        return obj.recipient == request.user
    
    def get_counterparty_name(self, obj):
        """Get the other party's name (for display in transaction list)."""
        request = self.context.get('request')
        if not request or not request.user:
            return None
        
        # If current user is sender, show recipient
        if obj.user == request.user:
            if obj.recipient:
                return f"{obj.recipient.first_name} {obj.recipient.last_name}".strip() or obj.recipient.email
            return "External"
        
        # If current user is recipient, show sender
        if obj.recipient == request.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email
        
        return None
    
    def get_counterparty_email(self, obj):
        """Get the other party's email."""
        request = self.context.get('request')
        if not request or not request.user:
            return None
        
        # If current user is sender, show recipient email
        if obj.user == request.user:
            return obj.recipient.email if obj.recipient else None
        
        # If current user is recipient, show sender email
        if obj.recipient == request.user:
            return obj.user.email
        
        return None
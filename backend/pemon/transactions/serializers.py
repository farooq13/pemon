from rest_framework import serializers
from decimal import Decimal

from .models import Transaction, LedgerEntry, TransactionType, TransactionStatus


class LedgerEntrySerializer(serializers.ModelSerializer):
    """
    Serializer for ledger entry details.
    """
    
    wallet_owner = serializers.EmailField(source='wallet.user.email', read_only=True)
    formatted_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = LedgerEntry
        fields = [
            'id',
            'entry_type',
            'amount',
            'formatted_amount',
            'balance_before',
            'balance_after',
            'wallet_owner',
            'description',
            'created_at',
        ]
        read_only_fields = fields
    
    def get_formatted_amount(self, obj):
        """Format amount with sign."""
        sign = '-' if obj.entry_type == 'DEBIT' else '+'
        return f"{sign}₦{obj.amount:,.2f}"


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
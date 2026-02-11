
from rest_framework import serializers
from decimal import Decimal

from .models import Wallet


class WalletBalanceSerializer(serializers.ModelSerializer):
    """
    Serializer for wallet balance information.
    
    Returns essential wallet information including balance,
    virtual account number, and status.
    """
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    formatted_balance = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = Wallet
        fields = [
            'id',
            'user_email',
            'user_name',
            'balance',
            'formatted_balance',
            'virtual_account_number',
            'is_frozen',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields
    
    def get_user_name(self, obj):
        """Get user's full name or email."""
        user = obj.user
        if hasattr(user, 'first_name') and hasattr(user, 'last_name'):
            full_name = f"{user.first_name} {user.last_name}".strip()
            return full_name if full_name else user.email
        return user.email
    
    def get_formatted_balance(self, obj):
        """Return formatted balance with currency symbol."""
        return f"₦{obj.balance:,.2f}"
    
    def get_status(self, obj):
        """Return wallet status."""
        if obj.is_frozen:
            return {
                'active': False,
                'message': 'Wallet is frozen',
                'reason': obj.freeze_reason or 'Contact support for details'
            }
        return {
            'active': True,
            'message': 'Wallet is active'
        }


class WalletDetailSerializer(serializers.ModelSerializer):
    """
    Detailed wallet serializer with additional information.
    
    Includes transaction statistics and KYC limits.
    """
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    formatted_balance = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    kyc_tier = serializers.SerializerMethodField()
    kyc_limits = serializers.SerializerMethodField()
    transaction_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Wallet
        fields = [
            'id',
            'user_email',
            'user_name',
            'balance',
            'formatted_balance',
            'virtual_account_number',
            'is_frozen',
            'freeze_reason',
            'status',
            'kyc_tier',
            'kyc_limits',
            'transaction_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields
    
    def get_user_name(self, obj):
        """Get user's full name or email."""
        user = obj.user
        if hasattr(user, 'first_name') and hasattr(user, 'last_name'):
            full_name = f"{user.first_name} {user.last_name}".strip()
            return full_name if full_name else user.email
        return user.email
    
    def get_formatted_balance(self, obj):
        """Return formatted balance with currency symbol."""
        return f"₦{obj.balance:,.2f}"
    
    def get_status(self, obj):
        """Return detailed wallet status."""
        if obj.is_frozen:
            return {
                'active': False,
                'message': 'Wallet is frozen',
                'reason': obj.freeze_reason or 'Contact support for details',
                'can_receive': False,
                'can_send': False,
            }
        return {
            'active': True,
            'message': 'Wallet is active',
            'can_receive': True,
            'can_send': True,
        }
    
    def get_kyc_tier(self, obj):
        """Get user's KYC tier."""
        try:
            kyc = obj.user.kyc
            return {
                'tier': kyc.tier,
                'status': kyc.status,
                'tier_name': kyc.get_tier_display() if hasattr(kyc, 'get_tier_display') else f"Tier {kyc.tier}"
            }
        except:
            return {
                'tier': 0,
                'status': 'unverified',
                'tier_name': 'Unverified'
            }
    
    def get_kyc_limits(self, obj):
        """Get KYC transaction limits."""
        try:
            kyc = obj.user.kyc
            limits = kyc.get_tier_limits()
            return {
                'daily_limit': str(limits.get('daily_limit', 0)),
                'single_transaction_limit': str(limits.get('single_transaction_limit', 0)),
                'total_balance_limit': str(limits.get('total_balance_limit', 0)),
                'formatted': {
                    'daily_limit': f"₦{limits.get('daily_limit', 0):,.2f}",
                    'single_transaction_limit': f"₦{limits.get('single_transaction_limit', 0):,.2f}",
                    'total_balance_limit': f"₦{limits.get('total_balance_limit', 0):,.2f}",
                }
            }
        except:
            return {
                'daily_limit': '0',
                'single_transaction_limit': '0',
                'total_balance_limit': '0',
                'formatted': {
                    'daily_limit': '₦0.00',
                    'single_transaction_limit': '₦0.00',
                    'total_balance_limit': '₦0.00',
                }
            }
    
    def get_transaction_count(self, obj):
        """Get total transaction count."""
        try:
            # Assuming you have reverse relations from Transaction model
            sent_count = obj.transactions_sent.count() if hasattr(obj, 'transactions_sent') else 0
            received_count = obj.transactions_received.count() if hasattr(obj, 'transactions_received') else 0
            return {
                'total': sent_count + received_count,
                'sent': sent_count,
                'received': received_count
            }
        except:
            return {
                'total': 0,
                'sent': 0,
                'received': 0
            }


class WalletFreezeSerializer(serializers.Serializer):
    """
    Serializer for wallet freeze/unfreeze operations.
    """
    
    reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Reason for freezing the wallet"
    )
    
    def validate_reason(self, value):
        """Validate freeze reason."""
        if self.context.get('action') == 'freeze' and not value:
            # Optionally require a reason when freezing
            # You can make this strict or lenient based on requirements
            pass
        return value
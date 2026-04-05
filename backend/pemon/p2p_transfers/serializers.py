from rest_framework import serializers
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError

from transactions.models import Transaction
from wallets.models import Wallet

User = get_user_model()


class P2PTransferSerializer(serializers.Serializer):
    """
    Serializer for peer-to-peer money transfers.
    
    Request Body:
        {```````````
            "recipient_identifier": "user@example.com" or "+2348012345678",
            "amount": "1000.00",
            "description": "Lunch money",
            "pin": "1234"  # Optional: Transaction PIN for security`
        }
    """
    
    recipient_identifier = serializers.CharField(
        max_length=255,
        required=True,
        help_text='Recipient email or phone number'
    )
    
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=True,
        help_text='Amount to transfer'
    )
    
    description = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text='Transfer description or note'
    )
    
    pin = serializers.CharField(
        max_length=6,
        required=False,
        allow_blank=True,
        write_only=True,
        help_text='Transaction PIN for security (optional)'
    )
    
    def validate_recipient_identifier(self, value):
        """
        Validate and find recipient user.
        
        Raises:
            serializers.ValidationError: If recipient not found
        """
        value = value.strip()
        
        # Try to find user by email or phone
        recipient = None
        
        if '@' in value:
            # Email lookup
            try:
                recipient = User.objects.get(email=value)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    f"No user found with email: {value}"
                )
        else:
            # Phone number lookup
            # Clean phone number (remove spaces, dashes)
            cleaned_phone = value.replace(' ', '').replace('-', '')
            
            try:
                recipient = User.objects.get(phone_number=cleaned_phone)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    f"No user found with phone number: {value}"
                )
        
        # Check if recipient has a wallet
        if not hasattr(recipient, 'wallet'):
            raise serializers.ValidationError(
                "Recipient does not have an active wallet. "
                "They need to complete KYC verification first."
            )
        
        # Store recipient in context for later use
        self.context['recipient'] = recipient
        
        return value
    
    def validate_amount(self, value):
        """
        Validate transfer amount.
        
        Raises:
            serializers.ValidationError: If amount invalid
        """
        # Check if positive
        if value <= 0:
            raise serializers.ValidationError(
                "Amount must be greater than zero"
            )
        
        # Check minimum transfer amount
        min_amount = Decimal('10.00')
        if value < min_amount:
            raise serializers.ValidationError(
                f"Minimum transfer amount is ₦{min_amount:,.2f}"
            )
        
        # Check maximum single transaction limit
        max_amount = Decimal('1000000.00')  # ₦1M
        if value > max_amount:
            raise serializers.ValidationError(
                f"Maximum single transfer amount is ₦{max_amount:,.2f}"
            )
        
        return value
    
    def validate(self, attrs):
        """
        Object-level validation.
        
        Validates:
        - User not sending to themselves
        - Sender has sufficient balance
        - Sender wallet not frozen
        - KYC limits
        """
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("Authentication required")
        
        sender = request.user
        recipient = self.context.get('recipient')
        amount = attrs.get('amount')
        
        # Check sender has wallet
        if not hasattr(sender, 'wallet'):
            raise serializers.ValidationError(
                "You don't have an active wallet. Please complete KYC verification."
            )
            
        # Check transfer PIN
        pin = attrs.get('pin')
        if not pin:
            raise serializers.ValidationError(
                "Transfer PIN is required."
            )
        if not sender.has_transfer_pin:
            raise serializers.ValidationError(
                "You have not set up a transfer PIN. Please set it up in Settings."
            )
        if not sender.check_transfer_pin(pin):
            raise serializers.ValidationError({
                "pin": "Incorrect transfer PIN."
            })

        
        sender_wallet = sender.wallet
        
        # Check sender not sending to themselves
        if sender.id == recipient.id:
            raise serializers.ValidationError(
                "You cannot transfer money to yourself"
            )
        
        # Check sender wallet not frozen
        if sender_wallet.is_frozen:
            raise serializers.ValidationError(
                f"Your wallet is frozen. Reason: {sender_wallet.freeze_reason or 'Contact support'}"
            )
        
        # Check sufficient balance
        if sender_wallet.balance < amount:
            raise serializers.ValidationError(
                f"Insufficient balance. Available: ₦{sender_wallet.balance:,.2f}, "
                f"Required: ₦{amount:,.2f}"
            )
        
        # Check KYC limits
        try:
            kyc = sender.kyc
            limits = kyc.get_tier_limits()
            
            # Check single transaction limit
            single_limit = Decimal(str(limits.get('single_transaction_limit', 0)))
            if amount > single_limit:
                raise serializers.ValidationError(
                    f"Amount exceeds your KYC tier limit of ₦{single_limit:,.2f}. "
                    f"Upgrade your KYC tier to send more."
                )
            
            # TODO: Check daily limit (requires tracking daily totals)
            
        except Exception as e:
            # If KYC not found or error, use conservative limit
            if amount > Decimal('50000.00'):
                raise serializers.ValidationError(
                    "Please complete KYC verification to send larger amounts"
                )
        
        return attrs


class TransferReceiptSerializer(serializers.ModelSerializer):
    """
    Serializer for transfer receipt/confirmation.
    
    Returns complete transaction details after successful transfer.
    """
    
    # Sender details
    sender_name = serializers.SerializerMethodField()
    sender_account = serializers.SerializerMethodField()
    sender_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()  # For compatibility
    user_account = serializers.SerializerMethodField()  # For compatibility
    
    # Recipient details
    recipient_name = serializers.SerializerMethodField()
    recipient_email = serializers.SerializerMethodField()
    recipient_account = serializers.SerializerMethodField()

    # Other fields
    formatted_amount = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    # Context fields
    is_debit = serializers.SerializerMethodField()
    counterparty_name = serializers.SerializerMethodField()
    counterparty_account = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'reference',
            'transaction_type',
            'amount',
            'formatted_amount',
            'status',
            'status_display',
            # Sender fields
            'sender_name',
            'sender_email',
            'sender_account',
            'user_name',
            'user_account',
            # Recipient fields
            'recipient_name',
            'recipient_email',
            'recipient_account',
            # Context fields
            'is_debit',
            'counterparty_name',
            'counterparty_account',
            'description',
            'created_at',
            'completed_at'
        ]
        read_only_fields = fields
    
    def get_sender_name(self, obj):
        """Get sender's name."""
        user = obj.user
        if hasattr(user, 'first_name') and hasattr(user, 'last_name'):
            full_name = f"{user.first_name} {user.last_name}".strip()
            return full_name if full_name else user.email
        return user.email
    
    def get_sender_account(self, obj):
        """Get sender's account number - ADDED."""
        if obj.user and hasattr(obj.user, 'wallet'):
            return obj.user.wallet.virtual_account_number
        return None
    
    def get_user_name(self, obj):
        """Get user (sender) name - for compatibility."""
        return self.get_sender_name(obj)
    
    def get_user_account(self, obj):
        """Get user (sender) account - for compatibility."""
        return self.get_sender_account(obj)
    
    def get_recipient_name(self, obj):
        """Get recipient's name."""
        if not obj.recipient:
            return None
        
        user = obj.recipient
        if hasattr(user, 'first_name') and hasattr(user, 'last_name'):
            full_name = f"{user.first_name} {user.last_name}".strip()
            return full_name if full_name else user.email
        return user.email
    
    def get_recipient_email(self, obj):
        """Get recipient email."""
        if obj.recipient:
            return obj.recipient.email
        return None
    
    def get_recipient_account(self, obj):
        """Get recipient's account number - ADDED."""
        if obj.recipient and hasattr(obj.recipient, 'wallet'):
            return obj.recipient.wallet.virtual_account_number
        return None
    
    def get_formatted_amount(self, obj):
        """Format amount with currency."""
        return f"₦{obj.amount:,.2f}"
    
    def get_is_debit(self, obj):
        """Check if this is a debit for current user."""
        request = self.context.get('request')
        if not request or not request.user:
            # Default to True (user is sender)
            return True
        return obj.user == request.user
    
    def get_counterparty_name(self, obj):
        """Get the other party's name."""
        request = self.context.get('request')
        if not request or not request.user:
            # Default to recipient
            return self.get_recipient_name(obj)
        
        if obj.user == request.user:
            # User is sender, return recipient
            return self.get_recipient_name(obj)
        else:
            # User is recipient, return sender
            return self.get_sender_name(obj)
    
    def get_counterparty_account(self, obj):
        """Get the other party's account number."""
        request = self.context.get('request')
        if not request or not request.user:
            # Default to recipient account
            return self.get_recipient_account(obj)
        
        if obj.user == request.user:
            # User is sender, return recipient account
            return self.get_recipient_account(obj)
        else:
            # User is recipient, return sender account
            return self.get_sender_account(obj)
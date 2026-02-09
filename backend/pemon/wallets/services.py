import logging
import random
from decimal import Decimal
from typing import Optional

from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .models import Wallet

User = get_user_model()
logger = logging.getLogger(__name__)


class WalletService:
    """
    Service class for wallet operations.
    
    Handles all wallet-related business logic including creation,
    balance management, and account status updates.
    """
    
    @staticmethod
    def generate_virtual_account_number() -> str:
        """
        Generate a unique 10-digit virtual account number.
        
        The virtual account number follows the format: 20XXXXXXXX
        where 20 is a prefix and X are random digits.
        
        Returns:
            str: 10-digit virtual account number
            
        Raises:
            RuntimeError: If unable to generate unique number after max attempts
        """
        max_attempts = 100
        prefix = "20"  # Pemon prefix
        
        for attempt in range(max_attempts):
            # Generate 8 random digits
            random_digits = ''.join([str(random.randint(0, 9)) for _ in range(8)])
            account_number = f"{prefix}{random_digits}"
            
            # Check uniqueness
            if not Wallet.objects.filter(virtual_account_number=account_number).exists():
                logger.info(f"Generated virtual account number: {account_number}")
                return account_number
        
        # If we couldn't generate a unique number after max attempts
        logger.error(f"Failed to generate unique virtual account after {max_attempts} attempts")
        raise RuntimeError("Unable to generate unique virtual account number")
    
    @staticmethod
    @transaction.atomic
    def create_wallet_for_user(user: User) -> Wallet:
        """
        Create a wallet for a user with initial balance of 0.00.
        
        This method ensures that:
        - Only one wallet exists per user
        - Virtual account number is unique
        - Wallet is created atomically
        
        """
        # Check if user already has a wallet
        if Wallet.objects.filter(user=user).exists():
            logger.warning(f"Attempted to create duplicate wallet for user {user.id}")
            raise ValidationError(f"User {user.email} already has a wallet")
        
        # Generate unique virtual account number
        virtual_account_number = WalletService.generate_virtual_account_number()
        
        # Create wallet
        wallet = Wallet.objects.create(
            user=user,
            balance=Decimal('0.00'),
            virtual_account_number=virtual_account_number,
            is_frozen=False
        )
        
        logger.info(
            f"Created wallet {wallet.id} for user {user.id} "
            f"with account number {virtual_account_number}"
        )
        
        return wallet
    
    @staticmethod
    def get_user_wallet(user: User) -> Optional[Wallet]:
        """
        Retrieve a user's wallet.
        
        Returns:
            Wallet or None: User's wallet if exists, None otherwise
        """
        try:
            return Wallet.objects.select_related('user').get(user=user)
        except Wallet.DoesNotExist:
            logger.warning(f"No wallet found for user {user.id}")
            return None
    
    @staticmethod
    @transaction.atomic
    def freeze_wallet(wallet: Wallet, reason: str = "") -> Wallet:
        """
        Freeze a wallet to prevent transactions.
        
        """
        if wallet.is_frozen:
            logger.warning(f"Wallet {wallet.id} is already frozen")
            return wallet
        
        wallet.is_frozen = True
        wallet.freeze_reason = reason
        wallet.save(update_fields=['is_frozen', 'freeze_reason', 'updated_at'])
        
        logger.warning(
            f"Wallet {wallet.id} (user: {wallet.user.email}) frozen. "
            f"Reason: {reason or 'Not specified'}"
        )
        
        return wallet
    
    @staticmethod
    @transaction.atomic
    def unfreeze_wallet(wallet: Wallet) -> Wallet:
        """
        Unfreeze a wallet to allow transactions.
        
        """
        if not wallet.is_frozen:
            logger.warning(f"Wallet {wallet.id} is not frozen")
            return wallet
        
        wallet.is_frozen = False
        wallet.freeze_reason = ""
        wallet.save(update_fields=['is_frozen', 'freeze_reason', 'updated_at'])
        
        logger.info(f"Wallet {wallet.id} (user: {wallet.user.email}) unfrozen")
        
        return wallet
    
    @staticmethod
    def is_wallet_active(wallet: Wallet) -> bool:
        """
        Check if wallet is active (not frozen).
        
        """
        return not wallet.is_frozen
    
    @staticmethod
    def get_wallet_balance(wallet: Wallet) -> Decimal:
        """
        Get the current balance of a wallet.
        
        """
        # Refresh from database to ensure we have the latest balance
        wallet.refresh_from_db()
        return wallet.balance


def create_wallet_on_kyc_approval(user: User) -> Optional[Wallet]:
    """
    Signal handler function to create wallet when KYC is approved.
    
    This function is called by a Django signal when a user's KYC
    status changes to 'approved'.
    
    Args:
        user (User): User whose KYC was approved
        
    Returns:
        Wallet or None: Created wallet or None if already exists
    """
    try:
        wallet = WalletService.create_wallet_for_user(user)
        logger.info(f"Auto-created wallet for user {user.id} after KYC approval")
        return wallet
    except ValidationError as e:
        # User already has a wallet
        logger.info(f"User {user.id} already has a wallet: {str(e)}")
        return None
    except Exception as e:
        logger.error(
            f"Error creating wallet for user {user.id} after KYC approval: {str(e)}",
            exc_info=True
        )
        return None
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from kyc.models import KYC
from .services import create_wallet_on_kyc_approval

logger = logging.getLogger(__name__)


@receiver(post_save, sender=KYC)
def create_wallet_on_kyc_approval_signal(sender, instance, created, **kwargs):
    """
    Signal to automatically create a wallet when KYC is approved.
    
    This signal listens for KYC model saves and creates a wallet
    when the status changes to 'approved'.
    
    """
    # Only process if KYC status is approved
    if instance.status == 'approved':
        # Check if wallet already exists to avoid duplicate signal processing
        if not hasattr(instance.user, 'wallet'):
            logger.info(
                f"KYC approved for user {instance.user.id}. "
                f"Triggering wallet creation."
            )
            create_wallet_on_kyc_approval(instance.user)
        else:
            logger.debug(
                f"KYC approved for user {instance.user.id}, "
                f"but wallet already exists."
            )
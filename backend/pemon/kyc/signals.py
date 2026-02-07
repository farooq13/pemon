import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import KYC

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=KYC)
def kyc_status_change_handler(sender, instance, **kwargs):
    """
    Handle KYC status changes before saving.
    
    Detects when status changes from pending to approved/rejected.
    """
    if instance.pk:
        try:
            old_instance = KYC.objects.get(pk=instance.pk)
            
            # Check if status changed
            if old_instance.status != instance.status:
                logger.info(
                    f'KYC status changed for user {instance.user.email}: '
                    f'{old_instance.status} -> {instance.status}'
                )
        except KYC.DoesNotExist:
            pass


@receiver(post_save, sender=KYC)
def kyc_approved_handler(sender, instance, created, **kwargs):
    """
    Handle actions when KYC is approved.
    
    - Create wallet if doesn't exist
    - Send approval notification email
    - Create audit log
    """
    if instance.status == KYC.Status.APPROVED and not created:
        logger.info(f'KYC approved for user {instance.user.email}, Tier: {instance.tier}')
        
        # Create wallet if it doesn't exist
        from wallets.models import Wallet
        
        if not hasattr(instance.user, 'wallet'):
            try:
                from core.utils import generate_virtual_account_number
                
                wallet = Wallet.objects.create(
                    user=instance.user,
                    virtual_account_number=generate_virtual_account_number(),
                    balance=0,
                    is_frozen=False,
                )
                logger.info(f'Wallet created for user {instance.user.email}: {wallet.virtual_account_number}')
            except Exception as e:
                logger.error(f'Failed to create wallet for {instance.user.email}: {e}')
        
        # Send approval notification email (async)
        try:
            from core.tasks import send_template_email_task
            
            send_template_email_task.delay(
                template_name='emails/kyc_approved.html',
                context={
                    'user_name': instance.user.get_full_name(),
                    'tier': instance.tier,
                    'tier_name': instance.get_tier_limits()['name'],
                    'daily_limit': instance.get_tier_limits()['daily_limit'],
                },
                subject='KYC Verification Approved - Pemon',
                recipient_list=[instance.user.email],
            )
            logger.info(f'Approval email queued for {instance.user.email}')
        except Exception as e:
            logger.error(f'Failed to queue approval email for {instance.user.email}: {e}')
        
        # Create audit log
        try:
            from core.models import AuditLog
            
            AuditLog.objects.create(
                user=instance.verified_by,
                action=AuditLog.ActionType.KYC_APPROVE,
                model_name='KYC',
                object_id=str(instance.id),
                changes={
                    'user_id': str(instance.user.id),
                    'user_email': instance.user.email,
                    'tier': instance.tier,
                    'status': instance.status,
                },
                metadata={
                    'verified_by': instance.verified_by.email if instance.verified_by else 'System',
                    'verified_at': instance.verified_at.isoformat() if instance.verified_at else None,
                }
            )
        except Exception as e:
            logger.error(f'Failed to create audit log: {e}')


@receiver(post_save, sender=KYC)
def kyc_rejected_handler(sender, instance, created, **kwargs):
    """
    Handle actions when KYC is rejected.
    
    - Send rejection notification email
    - Create audit log
    """
    if instance.status == KYC.Status.REJECTED and not created:
        logger.info(f'KYC rejected for user {instance.user.email}')
        
        # Send rejection notification email (async)
        try:
            from core.tasks import send_template_email_task
            
            send_template_email_task.delay(
                template_name='emails/kyc_rejected.html',
                context={
                    'user_name': instance.user.get_full_name(),
                    'rejection_reason': instance.rejection_reason or 'Please review your documents and try again.',
                },
                subject='KYC Verification Update - Pemon',
                recipient_list=[instance.user.email],
            )
            logger.info(f'Rejection email queued for {instance.user.email}')
        except Exception as e:
            logger.error(f'Failed to queue rejection email for {instance.user.email}: {e}')
        
        # Create audit log
        try:
            from core.models import AuditLog
            
            AuditLog.objects.create(
                user=instance.verified_by,
                action=AuditLog.ActionType.KYC_REJECT,
                model_name='KYC',
                object_id=str(instance.id),
                changes={
                    'user_id': str(instance.user.id),
                    'user_email': instance.user.email,
                    'status': instance.status,
                    'rejection_reason': instance.rejection_reason,
                },
                metadata={
                    'verified_by': instance.verified_by.email if instance.verified_by else 'System',
                    'verified_at': instance.verified_at.isoformat() if instance.verified_at else None,
                }
            )
        except Exception as e:
            logger.error(f'Failed to create audit log: {e}')


@receiver(post_save, sender=KYC)
def kyc_submitted_handler(sender, instance, created, **kwargs):
    """
    Handle actions when KYC is first submitted.
    
    - Send submission confirmation email
    - Notify admin (optional)
    """
    if created or (instance.status == KYC.Status.PENDING and instance.submitted_at):
        logger.info(f'KYC submitted for user {instance.user.email}')
        
        # Send submission confirmation email (async)
        try:
            from core.tasks import send_email_task
            
            send_email_task.delay(
                subject='KYC Verification Submitted - Pemon',
                message=f'Dear {instance.user.get_full_name()},\n\n'
                       f'Your KYC verification has been submitted successfully.\n\n'
                       f'Our team will review your documents and get back to you within 24-48 hours.\n\n'
                       f'Thank you for using Pemon!',
                recipient_list=[instance.user.email],
            )
            logger.info(f'Submission confirmation email queued for {instance.user.email}')
        except Exception as e:
            logger.error(f'Failed to queue submission email for {instance.user.email}: {e}')
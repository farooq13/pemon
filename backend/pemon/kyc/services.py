import logging
from datetime import timedelta
from decimal import Decimal
from typing import Dict, Tuple

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import KYC

User = get_user_model()
logger = logging.getLogger(__name__)


class KYCService:
    """Service class for KYC operations."""

    @staticmethod
    def get_or_create_kyc(user):
        """
        Get existing KYC or create new one for user.
        
        """
        kyc, created = KYC.objects.get_or_create(user=user)
        
        if created:
            logger.info(f'Created new KYC record for user {user.email}')
        
        return kyc, created

    @staticmethod
    @transaction.atomic
    def submit_kyc(user, kyc_data, id_document=None, selfie=None):
        """
        Submit KYC information for verification.
            
        Returns:
            KYC: Updated KYC instance
            
        Raises:
            ValueError: If validation fails
        """
        kyc, created = KYCService.get_or_create_kyc(user)
        
        # Validate submission
        if kyc.status == KYC.Status.APPROVED:
            raise ValueError('KYC already approved. Cannot resubmit.')
        
        if kyc.status == KYC.Status.PENDING:
            raise ValueError('KYC already pending review. Please wait for approval.')
        
        # Update KYC fields
        kyc.bvn = kyc_data.get('bvn', '')
        kyc.nin = kyc_data.get('nin', '')
        kyc.date_of_birth = kyc_data.get('date_of_birth')
        kyc.address = kyc_data.get('address', '')
        kyc.city = kyc_data.get('city', '')
        kyc.state = kyc_data.get('state', '')
        kyc.id_type = kyc_data.get('id_type', '')
        kyc.id_number = kyc_data.get('id_number', '')
        
        # Handle file uploads
        if id_document:
            kyc.id_document = id_document

        if selfie:
            kyc.selfie = selfie

        # Persist all updated fields (text fields and files) before marking submitted
        update_fields = [
            'bvn', 'nin', 'date_of_birth', 'address', 'city', 'state',
            'id_type', 'id_number', 'id_document', 'selfie', 'updated_at'
        ]
        kyc.save(update_fields=update_fields)

        # Mark as submitted (will set status and submitted_at)
        kyc.submit()
        
        logger.info(f'KYC submitted for user {user.email}')
        
        return kyc

    @staticmethod
    @transaction.atomic
    def approve_kyc(kyc_id, verified_by, tier=1):
        """
        Approve KYC and assign tier.
            
        Returns:
            KYC: Approved KYC instance
            
        Raises:
            ValueError: If tier is invalid
        """
        if tier not in [1, 2, 3]:
            raise ValueError('Invalid tier. Must be 1, 2, or 3.')
        
        kyc = KYC.objects.select_related('user').get(id=kyc_id)
        
        if kyc.status == KYC.Status.APPROVED:
            raise ValueError('KYC already approved.')
        
        kyc.approve(verified_by=verified_by, tier=tier)
        
        logger.info(
            f'KYC approved for user {kyc.user.email} '
            f'by {verified_by.email}, Tier: {tier}'
        )
        
        return kyc

    @staticmethod
    @transaction.atomic
    def reject_kyc(kyc_id, verified_by, reason):
        """
        Reject KYC with reason.
        
        Returns:
            KYC: Rejected KYC instance
        """
        kyc = KYC.objects.select_related('user').get(id=kyc_id)
        
        if kyc.status == KYC.Status.APPROVED:
            raise ValueError('Cannot reject already approved KYC.')
        
        kyc.reject(verified_by=verified_by, reason=reason)
        
        logger.info(
            f'KYC rejected for user {kyc.user.email} '
            f'by {verified_by.email}, Reason: {reason}'
        )
        
        return kyc

    @staticmethod
    def validate_bvn(bvn):
        """
        Validate BVN format.
            
        """
        if not bvn:
            return False, 'BVN is required'
        
        # Remove any spaces or dashes
        bvn = bvn.replace(' ', '').replace('-', '')
        
        if not bvn.isdigit():
            return False, 'BVN must contain only digits'
        
        if len(bvn) != 11:
            return False, 'BVN must be exactly 11 digits'
        
        return True, ''

    @staticmethod
    def validate_nin(nin):
        """
        Validate NIN format.
            
        """
        if not nin:
            return True, ''  # NIN is optional for Tier 1
        
        # Remove any spaces or dashes
        nin = nin.replace(' ', '').replace('-', '')
        
        if not nin.isdigit():
            return False, 'NIN must contain only digits'
        
        if len(nin) != 11:
            return False, 'NIN must be exactly 11 digits'
        
        return True, ''

    @staticmethod
    def check_daily_limit(user, amount):
        """
        Check if transaction amount is within daily limit.
        
        """
        try:
            kyc = user.kyc
            
            if kyc.status != KYC.Status.APPROVED:
                return False, 'KYC verification required'
            
            limits = kyc.get_tier_limits()
            
            # Check single transaction limit
            if amount > limits['single_transaction_limit']:
                return False, (
                    f'Amount exceeds single transaction limit of '
                    f'₦{limits["single_transaction_limit"]:,.2f}'
                )
            
            # Check daily limit
            from transactions.models import Transaction
            from django.db.models import Sum
            
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            today_total = Transaction.objects.filter(
                user=user,
                created_at__gte=today_start,
                status='COMPLETED'
            ).aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0')
            
            if today_total + amount > limits['daily_limit']:
                return False, (
                    f'Daily limit of ₦{limits["daily_limit"]:,.2f} would be exceeded. '
                    f'Available: ₦{(limits["daily_limit"] - today_total):,.2f}'
                )
            
            return True, ''
            
        except KYC.DoesNotExist:
            return False, 'KYC verification required'

    @staticmethod
    def get_kyc_status_summary(user):
        """
        Get comprehensive KYC status summary for user.
            
        Returns:
            dict: KYC status summary
        """
        try:
            kyc = user.kyc
            limits = kyc.get_tier_limits()
            
            return {
                'has_kyc': True,
                'tier': kyc.tier,
                'tier_name': limits['name'],
                'status': kyc.status,
                'status_display': kyc.get_status_display(),
                'is_approved': kyc.status == KYC.Status.APPROVED,
                'limits': {
                    'daily_limit': float(limits['daily_limit']),
                    'single_transaction_limit': float(limits['single_transaction_limit']),
                    'total_balance_limit': float(limits['total_balance_limit']),
                    'monthly_limit': float(limits['monthly_limit']),
                },
                'features': limits.get('features', []),
                'restrictions': limits.get('restrictions', []),
                'submitted_at': kyc.submitted_at.isoformat() if kyc.submitted_at else None,
                'verified_at': kyc.verified_at.isoformat() if kyc.verified_at else None,
                'rejection_reason': kyc.rejection_reason if kyc.status == KYC.Status.REJECTED else None,
            }
        except KYC.DoesNotExist:
            from .tier_limits import TIER_LIMITS
            tier_0_limits = TIER_LIMITS[0]
            
            return {
                'has_kyc': False,
                'tier': 0,
                'tier_name': tier_0_limits['name'],
                'status': 'NOT_SUBMITTED',
                'status_display': 'Not Submitted',
                'is_approved': False,
                'limits': {
                    'daily_limit': 0,
                    'single_transaction_limit': 0,
                    'total_balance_limit': 0,
                    'monthly_limit': 0,
                },
                'features': tier_0_limits.get('features', []),
                'restrictions': tier_0_limits.get('restrictions', []),
                'submitted_at': None,
                'verified_at': None,
                'rejection_reason': None,
            }
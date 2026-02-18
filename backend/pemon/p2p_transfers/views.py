import logging
from decimal import Decimal

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction as db_transaction
from django.contrib.auth import get_user_model

from .serializers import P2PTransferSerializer, TransferReceiptSerializer
from transactions.models import Transaction, TransactionType
from transactions.services import LedgerService
from transactions.utils import generate_idempotency_key

User = get_user_model()
logger = logging.getLogger(__name__)


class P2PTransferView(APIView):
    """
    POST /api/transfers/p2p/
    
    Process a peer-to-peer money transfer.
    
    """
    
    permission_classes = [IsAuthenticated]
    
    @db_transaction.atomic
    def post(self, request):
        """
        Process P2P transfer with double-entry ledger.
        """
        # Validate request data
        serializer = P2PTransferSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract validated data
        sender = request.user
        recipient = serializer.context['recipient']
        amount = serializer.validated_data['amount']
        description = serializer.validated_data.get('description', '')
        
        try:
            # Generate idempotency key to prevent duplicates
            idempotency_key = generate_idempotency_key(
                user_id=str(sender.id),
                transaction_type=TransactionType.TRANSFER,
                amount=str(amount),
                recipient_id=str(recipient.id)
            )
            
            # Create transaction
            txn = LedgerService.create_transaction(
                user=sender,
                transaction_type=TransactionType.TRANSFER,
                amount=amount,
                description=description or f"Transfer to {recipient.email}",
                recipient=recipient,
                idempotency_key=idempotency_key,
                metadata={
                    'transfer_type': 'p2p',
                    'sender_email': sender.email,
                    'recipient_email': recipient.email,
                }
            )
            
            # Check for duplicate (idempotency)
            if txn.status == 'COMPLETED':
                logger.warning(
                    f"Duplicate P2P transfer detected. "
                    f"Returning existing transaction {txn.reference}"
                )
                
                receipt_serializer = TransferReceiptSerializer(txn)
                return Response({
                    'status': 'success',
                    'message': 'Transfer already completed (duplicate request)',
                    'data': receipt_serializer.data
                }, status=status.HTTP_200_OK)
            
            # Get wallets
            sender_wallet = sender.wallet
            recipient_wallet = recipient.wallet
            
            # Process debit (sender)
            LedgerService.process_debit(
                txn=txn,
                wallet=sender_wallet,
                amount=amount,
                description=f"Transfer to {recipient.email}"
            )
            
            # Process credit (recipient)
            LedgerService.process_credit(
                txn=txn,
                wallet=recipient_wallet,
                amount=amount,
                description=f"Transfer from {sender.email}"
            )
            
            # Complete transaction
            completed_txn = LedgerService.complete_transaction(txn)
            
            # Verify ledger balance
            if not LedgerService.verify_ledger_balance(completed_txn):
                logger.error(
                    f"CRITICAL: Ledger imbalance detected for transaction {completed_txn.reference}"
                )
                # Still return success to user but log for investigation
            
            logger.info(
                f"P2P Transfer successful: {completed_txn.reference} - "
                f"₦{amount} from {sender.email} to {recipient.email}"
            )
            
            # Return receipt
            receipt_serializer = TransferReceiptSerializer(completed_txn)
            
            return Response({
                'status': 'success',
                'message': 'Transfer completed successfully',
                'data': receipt_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(
                f"P2P transfer failed: {str(e)}",
                exc_info=True,
                extra={
                    'sender': sender.email,
                    'recipient': recipient.email if 'recipient' in locals() else 'unknown',
                    'amount': amount
                }
            )
            
            # Mark transaction as failed if it exists
            if 'txn' in locals() and txn:
                try:
                    LedgerService.fail_transaction(txn, reason=str(e))
                except:
                    pass
            
            return Response({
                'status': 'error',
                'message': 'Transfer failed. Please try again.',
                'error_details': str(e) if request.user.is_staff else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_recipient(request):
    """
    POST /api/v1/transfers/validate-recipient/
    
    Validate a recipient by email or account number.
    Returns recipient details if found.
    """
    try:
        # Get identifier from request
        identifier = request.data.get('identifier', '').strip()
        
        if not identifier:
            return Response({
                'status': 'error',
                'message': 'Recipient identifier is required',
                'valid': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Validating recipient: {identifier}")
        
        # Import Wallet here to avoid circular import issues
        from wallets.models import Wallet
        
        user = None
        wallet = None
        
        # Determine if email or account number
        if '@' in identifier:
            # Email lookup
            try:
                user = User.objects.get(email=identifier)
            except User.DoesNotExist:
                logger.warning(f"User not found by email: {identifier}")
                return Response({
                    'status': 'error',
                    'message': 'Recipient not found',
                    'valid': False
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get wallet
            try:
                wallet = Wallet.objects.get(user=user)
            except Wallet.DoesNotExist:
                logger.warning(f"Wallet not found for user: {user.email}")
                return Response({
                    'status': 'error',
                    'message': 'Recipient wallet not found',
                    'valid': False
                }, status=status.HTTP_404_NOT_FOUND)
        
        else:
            # Account number lookup
            try:
                wallet = Wallet.objects.select_related('user').get(
                    virtual_account_number=identifier
                )
                user = wallet.user
            except Wallet.DoesNotExist:
                logger.warning(f"Wallet not found by account: {identifier}")
                return Response({
                    'status': 'error',
                    'message': 'Account number not found',
                    'valid': False
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if trying to send to self
        if user.id == request.user.id:
            return Response({
                'status': 'error',
                'message': 'Cannot send money to yourself',
                'valid': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if wallet is frozen
        if wallet.is_frozen:
            return Response({
                'status': 'error',
                'message': 'Recipient account is frozen',
                'valid': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Success - return recipient details
        logger.info(f"Validation successful for: {user.email}")
        
        return Response({
            'status': 'success',
            'valid': True,
            'recipient': {
                'id': str(user.id),
                'email': user.email,
                'first_name': getattr(user, 'first_name', '') or '',
                'last_name': getattr(user, 'last_name', '') or '',
                'account_number': wallet.virtual_account_number,
                'phone_number': getattr(user, 'phone_number', '') or '',
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.exception(f"Unexpected error in validate_recipient: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Server error: {str(e)}',
            'valid': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recent_recipients(request):
    """    
    Get list of recent transfer recipients for the authenticated user.
    """
    user = request.user
    
    # Get recent transactions where user is sender
    recent_transactions = Transaction.objects.filter(
        user=user,
        transaction_type=TransactionType.TRANSFER,
        recipient__isnull=False
    ).select_related('recipient').order_by('-created_at')[:10]
    
    # Build unique recipients list
    recipients = {}
    for txn in recent_transactions:
        if txn.recipient and txn.recipient.id not in recipients:
            try:
                recipient_wallet = Wallet.objects.get(user=txn.recipient)
                recipients[txn.recipient.id] = {
                    'email': txn.recipient.email,
                    'first_name': txn.recipient.first_name,
                    'last_name': txn.recipient.last_name,
                    'account_number': recipient_wallet.virtual_account_number,
                    'last_transaction_date': txn.created_at.isoformat(),
                }
            except Wallet.DoesNotExist:
                continue
    
    return Response({
        'status': 'success',
        'data': list(recipients.values())
    })
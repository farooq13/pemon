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
    
    Request Body:
        {
            "recipient_identifier": "user@example.com",
            "amount": "1000.00",
            "description": "Payment for lunch"
        }
    
    Returns:
        201: Transfer successful with transaction details
        400: Validation error
        500: Server error
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recent_recipients(request):
    """
    GET /api/transfers/recent-recipients/
    
    Get list of recent transfer recipients for autocomplete.
    
    Returns:
        200: List of recent recipients
    """
    user = request.user
    
    # Get recent transfers
    recent_transfers = Transaction.objects.filter(
        user=user,
        transaction_type=TransactionType.TRANSFER,
        status='COMPLETED'
    ).select_related('recipient').order_by('-created_at')[:10]
    
    # Extract unique recipients
    recipients = []
    seen_ids = set()
    
    for txn in recent_transfers:
        if txn.recipient and txn.recipient.id not in seen_ids:
            recipients.append({
                'id': str(txn.recipient.id),
                'email': txn.recipient.email,
                'phone_number': txn.recipient.phone_number,
                'name': (
                    f"{txn.recipient.first_name} {txn.recipient.last_name}".strip()
                    if hasattr(txn.recipient, 'first_name')
                    else txn.recipient.email
                ),
                'last_transfer_amount': str(txn.amount),
                'last_transfer_date': txn.created_at.isoformat()
            })
            seen_ids.add(txn.recipient.id)
    
    return Response({
        'status': 'success',
        'data': recipients
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_recipient(request):
    """
    POST /api/transfers/validate-recipient/
    
    Validate a recipient before showing transfer form.
    
    Request Body:
        {
            "identifier": "user@example.com" or "+2348012345678"
        }
    
    Returns:
        200: Recipient valid with details
        400: Recipient not found or invalid
    """
    identifier = request.data.get('identifier', '').strip()
    
    if not identifier:
        return Response({
            'status': 'error',
            'message': 'Recipient identifier is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Find user
    user = None
    if '@' in identifier:
        try:
            user = User.objects.get(email=identifier)
        except User.DoesNotExist:
            pass
    else:
        cleaned_phone = identifier.replace(' ', '').replace('-', '')
        try:
            user = User.objects.get(phone_number=cleaned_phone)
        except User.DoesNotExist:
            pass
    
    if not user:
        return Response({
            'status': 'error',
            'message': 'Recipient not found',
            'valid': False
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check if has wallet
    if not hasattr(user, 'wallet'):
        return Response({
            'status': 'error',
            'message': 'Recipient has not completed KYC verification',
            'valid': False
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if user trying to send to themselves
    if user.id == request.user.id:
        return Response({
            'status': 'error',
            'message': 'You cannot send money to yourself',
            'valid': False
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Return recipient details
    return Response({
        'status': 'success',
        'valid': True,
        'data': {
            'id': str(user.id),
            'email': user.email,
            'phone_number': user.phone_number,
            'name': (
                f"{user.first_name} {user.last_name}".strip()
                if hasattr(user, 'first_name')
                else user.email
            ),
        }
    })
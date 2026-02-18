from django.shortcuts import render

  
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from django.db import transaction as db_transaction
from django.contrib.auth import get_user_model
from decimal import Decimal

from .models import Wallet
from transactions.models import Transaction, TransactionType
from transactions.services import LedgerService
from .serializers import (
    WalletBalanceSerializer,
    WalletDetailSerializer,
    WalletFreezeSerializer
)
from .services import WalletService

logger = logging.getLogger(__name__)
User = get_user_model()


class WalletBalanceView(APIView):
    """  
    Retrieve the authenticated user's wallet balance.
    
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get wallet balance for authenticated user.
        
        Returns wallet balance, virtual account number, and status.
        """
        try:
            wallet = Wallet.objects.select_related('user').get(user=request.user)
            serializer = WalletBalanceSerializer(wallet)
            
            logger.info(f"User {request.user.id} retrieved wallet balance")
            
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Wallet.DoesNotExist:
            logger.warning(
                f"User {request.user.id} attempted to access wallet but none exists"
            )
            return Response({
                'status': 'error',
                'message': 'Wallet not found. Please complete KYC verification.',
                'error_code': 'WALLET_NOT_FOUND'
            }, status=status.HTTP_404_NOT_FOUND)


class WalletDetailView(APIView):
    """  
    Retrieve detailed wallet information including limits and statistics.
    
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get detailed wallet information for authenticated user.
        
        Returns comprehensive wallet data including KYC limits,
        transaction counts, and status.
        """
        try:
            wallet = Wallet.objects.select_related('user', 'user__kyc').get(
                user=request.user
            )
            serializer = WalletDetailSerializer(wallet)
            
            logger.info(f"User {request.user.id} retrieved detailed wallet info")
            
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Wallet.DoesNotExist:
            logger.warning(
                f"User {request.user.id} attempted to access wallet details but none exists"
            )
            return Response({
                'status': 'error',
                'message': 'Wallet not found. Please complete KYC verification.',
                'error_code': 'WALLET_NOT_FOUND'
            }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def freeze_wallet(request, wallet_id):
    """
    Freeze a user's wallet to prevent transactions.
    
    """
    wallet = get_object_or_404(Wallet, id=wallet_id)
    
    serializer = WalletFreezeSerializer(
        data=request.data,
        context={'action': 'freeze'}
    )
    
    if not serializer.is_valid():
        return Response({
            'status': 'error',
            'message': 'Invalid request data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    reason = serializer.validated_data.get('reason', 'Frozen by admin')
    
    # Check if already frozen
    if wallet.is_frozen:
        return Response({
            'status': 'error',
            'message': 'Wallet is already frozen',
            'error_code': 'ALREADY_FROZEN'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Freeze the wallet
    frozen_wallet = WalletService.freeze_wallet(wallet, reason)
    
    logger.warning(
        f"Admin {request.user.id} froze wallet {wallet_id}. Reason: {reason}"
    )
    
    return Response({
        'status': 'success',
        'message': 'Wallet frozen successfully',
        'data': {
            'wallet_id': str(frozen_wallet.id),
            'user_email': frozen_wallet.user.email,
            'is_frozen': frozen_wallet.is_frozen,
            'freeze_reason': frozen_wallet.freeze_reason
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def unfreeze_wallet(request, wallet_id):
    """    
    Unfreeze a user's wallet to allow transactions.
    
    """
    wallet = get_object_or_404(Wallet, id=wallet_id)
    
    # Check if not frozen
    if not wallet.is_frozen:
        return Response({
            'status': 'error',
            'message': 'Wallet is not frozen',
            'error_code': 'NOT_FROZEN'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Unfreeze the wallet
    unfrozen_wallet = WalletService.unfreeze_wallet(wallet)
    
    logger.info(
        f"Admin {request.user.id} unfroze wallet {wallet_id}"
    )
    
    return Response({
        'status': 'success',
        'message': 'Wallet unfrozen successfully',
        'data': {
            'wallet_id': str(unfrozen_wallet.id),
            'user_email': unfrozen_wallet.user.email,
            'is_frozen': unfrozen_wallet.is_frozen
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_wallet_status(request):
    """    
    Quick check if user has a wallet and its status.
    
    """
    try:
        wallet = Wallet.objects.get(user=request.user)
        
        return Response({
            'status': 'success',
            'data': {
                'has_wallet': True,
                'is_active': not wallet.is_frozen,
                'is_frozen': wallet.is_frozen,
                'freeze_reason': wallet.freeze_reason if wallet.is_frozen else None
            }
        }, status=status.HTTP_200_OK)
        
    except Wallet.DoesNotExist:
        return Response({
            'status': 'success',
            'data': {
                'has_wallet': False,
                'message': 'Complete KYC verification to get a wallet'
            }
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminUser])
@db_transaction.atomic
def admin_credit_wallet(request):
    """
    Admin endpoint to manually credit a user's wallet (for testing/support).
    
    """
    user_email = request.data.get('user_email')
    amount = request.data.get('amount')
    description = request.data.get('description', 'Admin credit')
    
    # Validate inputs
    if not user_email or not amount:
        return Response({
            'status': 'error',
            'message': 'user_email and amount are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except (ValueError, decimal.InvalidOperation):
        return Response({
            'status': 'error',
            'message': 'Invalid amount. Must be a positive number'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get user
    try:
        user = User.objects.get(email=user_email)
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': f'User with email {user_email} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Get wallet
    try:
        wallet = user.wallet
    except:
        return Response({
            'status': 'error',
            'message': f'User {user_email} does not have a wallet'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Create deposit transaction
    txn = LedgerService.create_transaction(
        user=user,
        transaction_type=TransactionType.DEPOSIT,
        amount=amount,
        description=description,
        metadata={
            'source': 'admin_credit',
            'admin_user': request.user.email,
        }
    )
    
    # Credit the wallet
    LedgerService.process_credit(
        txn=txn,
        wallet=wallet,
        amount=amount,
        description=description
    )
    
    # Complete transaction
    LedgerService.complete_transaction(txn)
    
    return Response({
        'status': 'success',
        'message': f'Successfully credited ₦{amount:,.2f} to {user_email}',
        'data': {
            'user_email': user_email,
            'amount': str(amount),
            'previous_balance': str(txn.ledger_entries.first().balance_before),
            'new_balance': str(wallet.balance),
            'transaction_reference': txn.reference
        }
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
@db_transaction.atomic
def admin_debit_wallet(request):
    """
    Admin endpoint to manually debit a user's wallet.
    
    """
    user_email = request.data.get('user_email')
    amount = request.data.get('amount')
    description = request.data.get('description', 'Admin debit')
    
    if not user_email or not amount:
        return Response({
            'status': 'error',
            'message': 'user_email and amount are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except (ValueError, decimal.InvalidOperation):
        return Response({
            'status': 'error',
            'message': 'Invalid amount'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=user_email)
        wallet = user.wallet
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': f'User {user_email} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except:
        return Response({
            'status': 'error',
            'message': f'Wallet not found for {user_email}'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check sufficient balance
    if wallet.balance < amount:
        return Response({
            'status': 'error',
            'message': f'Insufficient balance. Available: ₦{wallet.balance:,.2f}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Create withdrawal transaction
    txn = LedgerService.create_transaction(
        user=user,
        transaction_type=TransactionType.WITHDRAWAL,
        amount=amount,
        description=description,
        metadata={
            'source': 'admin_debit',
            'admin_user': request.user.email,
        }
    )
    
    # Debit the wallet
    LedgerService.process_debit(
        txn=txn,
        wallet=wallet,
        amount=amount,
        description=description
    )
    
    # Complete transaction
    LedgerService.complete_transaction(txn)
    
    return Response({
        'status': 'success',
        'message': f'Successfully debited ₦{amount:,.2f} from {user_email}',
        'data': {
            'user_email': user_email,
            'amount': str(amount),
            'previous_balance': str(txn.ledger_entries.first().balance_before),
            'new_balance': str(wallet.balance),
            'transaction_reference': txn.reference
        }
    })


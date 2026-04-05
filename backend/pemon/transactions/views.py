import logging
from datetime import datetime, timedelta
from decimal import Decimal

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Sum, Count
from django.utils import timezone
from rest_framework.filters import SearchFilter

from .models import Transaction, LedgerEntry, TransactionStatus, TransactionType
from .serializers import (
    TransactionListSerializer,
    TransactionDetailSerializer,
    TransactionStatsSerializer,
    TransactionSerializer,
)

from django.http import HttpResponse, FileResponse
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.db import transaction as db_transaction

from transactions.models import Transaction
from transactions.services import LedgerService
from transactions.receipts import generate_transaction_receipt, generate_receipt_html
from .exports import export_transactions_csv

logger = logging.getLogger(__name__)


class TransactionPagination(PageNumberPagination):
    """Custom pagination for transactions."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class TransactionListView(ListAPIView):
    """
    List user's transactions with filtering and pagination.
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionListSerializer
    pagination_class = TransactionPagination

    filter_backends = [SearchFilter] 
    search_fields = [  
        'reference',
        'description',
        'user__email',
        'recipient__email',
    ]
    
    def get_queryset(self):
        """
        Get user's transactions with filters.
        """
        user = self.request.user
        queryset = Transaction.objects.filter(
            Q(user=user) | Q(recipient=user)
        ).select_related('user', 'recipient').prefetch_related('ledger_entries')
        
        # Filter by transaction type
        transaction_type = self.request.query_params.get('type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type.upper())
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                queryset = queryset.filter(created_at__gte=start)
            except ValueError:
                pass
        
        end_date = self.request.query_params.get('end_date')
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d')
                # Include the entire end date
                end = end.replace(hour=23, minute=59, second=59)
                queryset = queryset.filter(created_at__lte=end)
            except ValueError:
                pass
        
        # Search in reference or description
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(reference__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        """Override list to add custom response format."""
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'status': 'success',
                'data': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data
        })


class TransactionDetailView(RetrieveAPIView):
    """
    Get detailed information about a specific transaction.
    
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionDetailSerializer
    lookup_field = 'id'
    
    def get_queryset(self):
        """
        Get user's transactions only.
        """
        user = self.request.user
        return Transaction.objects.filter(
            Q(user=user) | Q(recipient=user)
        ).select_related(
            'user',
            'recipient',
            'reversed_by',
            'original_transaction'
        ).prefetch_related('ledger_entries')
    
    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to add custom response format."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response({
            'status': 'success',
            'data': serializer.data
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transaction_stats(request):
    """    
    Get transaction statistics for the user.
    """
    user = request.user
    period = request.query_params.get('period', '30d')
    
    # Calculate date range
    now = timezone.now()
    if period == '7d':
        start_date = now - timedelta(days=7)
    elif period == '30d':
        start_date = now - timedelta(days=30)
    elif period == '90d':
        start_date = now - timedelta(days=90)
    elif period == '1y':
        start_date = now - timedelta(days=365)
    else:  # 'all'
        start_date = None
    
    # Base queryset
    queryset = Transaction.objects.filter(
        Q(user=user) | Q(recipient=user),
        status=TransactionStatus.COMPLETED
    )
    
    if start_date:
        queryset = queryset.filter(created_at__gte=start_date)
    
    # Get user's wallet
    try:
        wallet = user.wallet
    except:
        wallet = None
    
    # Calculate debits and credits from ledger entries
    if wallet:
        ledger_queryset = LedgerEntry.objects.filter(
            wallet=wallet,
            transaction__status=TransactionStatus.COMPLETED
        )
        
        if start_date:
            ledger_queryset = ledger_queryset.filter(created_at__gte=start_date)
        
        total_debits = ledger_queryset.filter(
            entry_type='DEBIT'
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        total_credits = ledger_queryset.filter(
            entry_type='CREDIT'
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
    else:
        total_debits = Decimal('0')
        total_credits = Decimal('0')
    
    # Net flow
    net_flow = total_credits - total_debits
    
    # Breakdown by type
    by_type = {}
    type_stats = queryset.values('transaction_type').annotate(
        count=Count('id'),
        total=Sum('amount')
    )
    
    for stat in type_stats:
        type_name = stat['transaction_type']
        by_type[type_name] = {
            'count': stat['count'],
            'total': str(stat['total'] or 0),
            'total_formatted': f"₦{stat['total'] or 0:,.2f}"
        }
    
    # Recent transactions
    recent = queryset.order_by('-created_at')[:5]
    recent_serializer = TransactionListSerializer(
        recent,
        many=True,
        context={'request': request}
    )
    
    # Build response
    stats_data = {
        'total_transactions': queryset.count(),
        'total_debits': total_debits,
        'total_credits': total_credits,
        'total_debits_formatted': f"₦{total_debits:,.2f}",
        'total_credits_formatted': f"₦{total_credits:,.2f}",
        'net_flow': net_flow,
        'net_flow_formatted': f"₦{net_flow:,.2f}",
        'by_type': by_type,
        'recent_transactions': recent_serializer.data
    }
    
    return Response({
        'status': 'success',
        'data': stats_data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transaction_summary(request):
    """
    GET /api/transactions/summary/
    
    Get a quick summary of user's transactions.
    
    Returns:
        200: Transaction summary
    """
    user = request.user
    
    try:
        wallet = user.wallet
    except:
        return Response({
            'status': 'error',
            'message': 'Wallet not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Count by status
    pending = Transaction.objects.filter(
        user=user,
        status=TransactionStatus.PENDING
    ).count()
    
    completed = Transaction.objects.filter(
        user=user,
        status=TransactionStatus.COMPLETED
    ).count()
    
    failed = Transaction.objects.filter(
        user=user,
        status=TransactionStatus.FAILED
    ).count()
    
    # Today's transactions
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = Transaction.objects.filter(
        Q(user=user) | Q(recipient=user),
        created_at__gte=today_start
    ).count()
    
    return Response({
        'status': 'success',
        'data': {
            'pending': pending,
            'completed': completed,
            'failed': failed,
            'today_count': today_count,
            'current_balance': str(wallet.balance),
            'current_balance_formatted': f"₦{wallet.balance:,.2f}"
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_receipt(request, transaction_id):
    """
    GET /api/transactions/<id>/receipt/
    
    Download transaction receipt as PDF.
    
    Query Parameters:
        format: 'pdf' (default) or 'html'
    
    Returns:
        200: PDF or HTML receipt
        403: User not authorized
        404: Transaction not found
    """
    # Get transaction
    txn = get_object_or_404(
        Transaction.objects.select_related('user', 'recipient'),
        id=transaction_id
    )
    
    # Check authorization - user must be sender or recipient
    if txn.user != request.user and txn.recipient != request.user:
        return Response({
            'status': 'error',
            'message': 'You are not authorized to view this receipt'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get format
    format_type = request.query_params.get('format', 'pdf').lower()
    
    if format_type == 'html':
        # Return HTML receipt
        html_content = generate_receipt_html(txn)
        return HttpResponse(html_content, content_type='text/html')
    
    else:
        # Generate PDF receipt
        pdf_buffer = generate_transaction_receipt(txn)
        
        # Return PDF as download
        response = FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename=f'receipt_{txn.reference}.pdf',
            content_type='application/pdf'
        )
        
        logger.info(
            f"Receipt downloaded for transaction {txn.reference} by user {request.user.id}"
        )
        
        return response


@api_view(['POST'])
@permission_classes([IsAdminUser])
@db_transaction.atomic
def reverse_transaction(request, transaction_id):
    """ 
    Reverse a completed transaction (Admin only).
    
    """
    # Get transaction
    txn = get_object_or_404(Transaction, id=transaction_id)
    
    # Get reversal reason
    reason = request.data.get('reason', 'Admin reversal')
    
    # Validate transaction can be reversed
    if not txn.can_be_reversed:
        return Response({
            'status': 'error',
            'message': f'Transaction cannot be reversed. Status: {txn.status}',
            'can_reverse': False,
            'details': {
                'current_status': txn.status,
                'already_reversed': txn.is_reversed,
                'transaction_type': txn.transaction_type
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Perform reversal
        reversal_txn = LedgerService.reverse_transaction(
            original_txn=txn,
            reversed_by_user=request.user,
            reason=reason
        )
        
        logger.warning(
            f"Transaction {txn.reference} reversed by admin {request.user.email}. "
            f"Reversal ref: {reversal_txn.reference}, Reason: {reason}"
        )
        
        return Response({
            'status': 'success',
            'message': 'Transaction reversed successfully',
            'data': {
                'original_transaction': {
                    'id': str(txn.id),
                    'reference': txn.reference,
                    'amount': str(txn.amount),
                    'status': txn.status
                },
                'reversal_transaction': {
                    'id': str(reversal_txn.id),
                    'reference': reversal_txn.reference,
                    'amount': str(reversal_txn.amount),
                    'status': reversal_txn.status,
                    'created_at': reversal_txn.created_at.isoformat()
                },
                'reason': reason
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(
            f"Failed to reverse transaction {txn.reference}: {str(e)}",
            exc_info=True
        )
        
        return Response({
            'status': 'error',
            'message': 'Reversal failed. Please try again.',
            'error_details': str(e) if request.user.is_staff else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_transaction_history(request):
    """
    GET /api/v1/transactions/
    
    Get transaction history for authenticated user.
    Shows all transactions where user is sender OR recipient.
    
    Query Parameters:
        page: Page number (default: 1)
        page_size: Items per page (default: 20)
        status: Filter by status (PENDING, COMPLETED, FAILED)
        type: Filter by type (TRANSFER, DEPOSIT, WITHDRAWAL, etc)
        search: Search by reference or description
    """
    user = request.user
    
    # Get all transactions where user is involved (as sender or recipient)
    transactions = Transaction.objects.filter(
        Q(user=user) | Q(recipient=user)
    ).select_related('user', 'recipient').order_by('-created_at')
    
    # Apply filters
    status_filter = request.query_params.get('status')
    if status_filter:
        transactions = transactions.filter(status=status_filter.upper())
    
    type_filter = request.query_params.get('type')
    if type_filter:
        transactions = transactions.filter(transaction_type=type_filter.upper())
    
    search = request.query_params.get('search')
    if search:
        transactions = transactions.filter(
            Q(reference__icontains=search) | 
            Q(description__icontains=search)
        )
    
    # Pagination
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    
    start = (page - 1) * page_size
    end = start + page_size
    
    total_count = transactions.count()
    paginated_transactions = transactions[start:end]
    
    # Serialize with context
    serializer = TransactionSerializer(
        paginated_transactions, 
        many=True,
        context={'request': request}
    )
    
    return Response({
        'status': 'success',
        'data': serializer.data,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total_count': total_count,
            'total_pages': (total_count + page_size - 1) // page_size,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_transaction_detail(request, transaction_id):
    """
    GET /api/v1/transactions/<id>/
    
    Get detailed information about a specific transaction.
    User must be involved in the transaction (sender or recipient).
    """
    user = request.user
    
    try:
        transaction = Transaction.objects.select_related(
            'user', 'recipient'
        ).prefetch_related('ledger_entries').get(
            Q(id=transaction_id) & (Q(user=user) | Q(recipient=user))
        )
    except Transaction.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Transaction not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = TransactionSerializer(transaction, context={'request': request})
    
    return Response({
        'status': 'success',
        'data': serializer.data
    })

# Export Transactions
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_transactions(request):
    '''
    Export user's transactions to CSV.
    '''
    user = request.user
    
    # Base queryset - user's transactions
    queryset = Transaction.objects.filter(
        Q(user=user) | Q(recipient=user)
    )
    
    # Apply filters
    start_date = request.query_params.get('start_date')
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            queryset = queryset.filter(created_at__gte=start)
        except ValueError:
            pass
    
    end_date = request.query_params.get('end_date')
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            # Include entire end date
            end = end.replace(hour=23, minute=59, second=59)
            queryset = queryset.filter(created_at__lte=end)
        except ValueError:
            pass
    
    transaction_type = request.query_params.get('type')
    if transaction_type:
        queryset = queryset.filter(transaction_type=transaction_type.upper())
    
    status_filter = request.query_params.get('status')
    if status_filter:
        queryset = queryset.filter(status=status_filter.upper())
    
    # Order by date descending
    queryset = queryset.order_by('-created_at')
    
    # Generate and return CSV
    return export_transactions_csv(queryset)

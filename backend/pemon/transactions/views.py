import logging
from datetime import datetime, timedelta
from decimal import Decimal

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Sum, Count
from django.utils import timezone

from .models import Transaction, LedgerEntry, TransactionStatus, TransactionType
from .serializers import (
    TransactionListSerializer,
    TransactionDetailSerializer,
    TransactionStatsSerializer
)

logger = logging.getLogger(__name__)


class TransactionPagination(PageNumberPagination):
    """Custom pagination for transactions."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class TransactionListView(ListAPIView):
    """
    GET /api/transactions/
    
    List user's transactions with filtering and pagination.
    
    Query Parameters:
        - page: Page number
        - page_size: Items per page (max 100)
        - type: Filter by transaction type
        - status: Filter by status
        - start_date: Filter from date (YYYY-MM-DD)
        - end_date: Filter to date (YYYY-MM-DD)
        - search: Search in reference or description
    
    Returns:
        200: Paginated list of transactions
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionListSerializer
    pagination_class = TransactionPagination
    
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
    GET /api/transactions/<id>/
    
    Get detailed information about a specific transaction.
    
    Returns:
        200: Transaction details with ledger entries
        403: User not authorized to view this transaction
        404: Transaction not found
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
    GET /api/transactions/stats/
    
    Get transaction statistics for the user.
    
    Query Parameters:
        - period: Time period (7d, 30d, 90d, 1y, all) - default: 30d
    
    Returns:
        200: Transaction statistics
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
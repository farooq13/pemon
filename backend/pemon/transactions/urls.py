from django.urls import path
from .views import (
    TransactionListView,
    TransactionDetailView,
    transaction_stats,
    transaction_summary,
)

app_name = 'transactions'

urlpatterns = [
    # List and details
    path('', TransactionListView.as_view(), name='transaction-list'),
    path('<uuid:id>/', TransactionDetailView.as_view(), name='transaction-detail'),
    
    # Statistics and summaries
    path('stats/', transaction_stats, name='transaction-stats'),
    path('summary/', transaction_summary, name='transaction-summary'),
]
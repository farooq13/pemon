from django.urls import path
from .views import (
    WalletBalanceView,
    WalletDetailView,
    freeze_wallet,
    unfreeze_wallet,
    check_wallet_status,
)

app_name = 'wallets'

urlpatterns = [
    # User endpoints
    path('balance/', WalletBalanceView.as_view(), name='wallet-balance'),
    path('detail/', WalletDetailView.as_view(), name='wallet-detail'),
    path('status/', check_wallet_status, name='wallet-status'),
    
    # Admin endpoints
    path('<uuid:wallet_id>/freeze/', freeze_wallet, name='wallet-freeze'),
    path('<uuid:wallet_id>/unfreeze/', unfreeze_wallet, name='wallet-unfreeze'),
]

from django.urls import path
from .views import (
    P2PTransferView,
    get_recent_recipients,
    validate_recipient,
)

app_name = 'transfers'

urlpatterns = [
    # P2P Transfer
    path('p2p/', P2PTransferView.as_view(), name='p2p-transfer'),
    
    # Helper endpoints
    path('recent-recipients/', get_recent_recipients, name='recent-recipients'),
    path('validate-recipient/', validate_recipient, name='validate-recipient'),
]

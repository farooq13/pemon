from django.urls import path

from .views import (
    KYCDetailView,
    KYCStatusView,
    KYCSubmissionView,
    TierComparisonView,
    TransactionEligibilityView,
)

app_name = 'kyc'

urlpatterns = [
    # KYC submission and status
    path('submit/', KYCSubmissionView.as_view(), name='submit'),
    path('status/', KYCStatusView.as_view(), name='status'),
    path('detail/', KYCDetailView.as_view(), name='detail'),
    
    # Tier information
    path('tiers/', TierComparisonView.as_view(), name='tiers'),
    
    # Transaction eligibility check
    path('check-eligibility/', TransactionEligibilityView.as_view(), name='check-eligibility'),
]
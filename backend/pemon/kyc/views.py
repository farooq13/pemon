from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import KYC
from .serializers import (
    KYCDetailSerializer,
    KYCStatusSerializer,
    KYCSubmissionSerializer,
)
from .services import KYCService
from .tier_limits import get_tier_comparison


@extend_schema_view(
    post=extend_schema(
        summary="Submit KYC verification",
        description="Submit KYC information for verification. Requires BVN, ID document, and selfie.",
        tags=['KYC'],
    )
)
class KYCSubmissionView(generics.CreateAPIView):
    """
    API endpoint for KYC submission.
    
    """
    
    serializer_class = KYCSubmissionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Handle KYC submission."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            kyc = serializer.save()
        except ValueError as e:
            # Catch business logic errors from services and return 400
            return Response(
                {
                    'detail': str(e),
                    'error': {
                        'message': str(e),
                        'code': 'kyc_submission_error',
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(
            {
                'message': 'KYC submitted successfully. Your application is under review.',
                'kyc': KYCStatusSerializer(kyc).data,
            },
            status=status.HTTP_201_CREATED
        )


@extend_schema_view(
    get=extend_schema(
        summary="Get KYC status",
        description="Retrieve current KYC verification status and tier information.",
        tags=['KYC'],
    )
)
class KYCStatusView(generics.RetrieveAPIView):
    """
    API endpoint for KYC status.
    
    """
    
    serializer_class = KYCStatusSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Get or create KYC for current user."""
        kyc, created = KYCService.get_or_create_kyc(self.request.user)
        return kyc


@extend_schema_view(
    get=extend_schema(
        summary="Get detailed KYC information",
        description="Retrieve detailed KYC information including documents and verification history.",
        tags=['KYC'],
    )
)
class KYCDetailView(generics.RetrieveAPIView):
    """
    API endpoint for detailed KYC information.
    
    Returns complete KYC information including uploaded documents.
    """
    
    serializer_class = KYCDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Get KYC for current user."""
        try:
            return self.request.user.kyc
        except KYC.DoesNotExist:
            # Return empty KYC if doesn't exist
            return KYC(user=self.request.user)


@extend_schema(
    summary="Get tier comparison",
    description="Get comparison of all KYC tiers with limits and features.",
    tags=['KYC'],
)
class TierComparisonView(APIView):
    """
    API endpoint for tier comparison.
    
    Returns comparison of all KYC tiers.

    """
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return tier comparison."""
        tiers = get_tier_comparison()
        return Response(tiers, status=status.HTTP_200_OK)


@extend_schema(
    summary="Check transaction eligibility",
    description="Check if user can perform a transaction of given amount.",
    tags=['KYC'],
)
class TransactionEligibilityView(APIView):
    """
    API endpoint to check transaction eligibility.
    
    Check if user can perform a transaction based on KYC limits.
    
    """
    
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Check transaction eligibility."""
        from decimal import Decimal
        
        amount = request.data.get('amount')
        
        if not amount:
            return Response(
                {'error': 'Amount is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount = Decimal(str(amount))
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid amount format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check eligibility
        can_transact, reason = KYCService.check_daily_limit(request.user, amount)
        
        # Get KYC info
        try:
            kyc = request.user.kyc
            limits = kyc.get_tier_limits()
            
            response_data = {
                'can_transact': can_transact,
                'reason': reason,
                'current_tier': kyc.tier,
                'tier_name': limits['name'],
                'limits': {
                    'daily_limit': float(limits['daily_limit']),
                    'single_transaction_limit': float(limits['single_transaction_limit']),
                    'daily_limit_formatted': f"₦{limits['daily_limit']:,.2f}",
                    'single_transaction_limit_formatted': f"₦{limits['single_transaction_limit']:,.2f}",
                },
            }
        except KYC.DoesNotExist:
            response_data = {
                'can_transact': False,
                'reason': 'KYC verification required',
                'current_tier': 0,
                'tier_name': 'Unverified',
                'limits': {
                    'daily_limit': 0,
                    'single_transaction_limit': 0,
                },
            }
        
        return Response(response_data, status=status.HTTP_200_OK)
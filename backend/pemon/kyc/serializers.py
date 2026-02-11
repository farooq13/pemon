from rest_framework import serializers

from .models import KYC, KYCDocument
from .services import KYCService


class KYCSubmissionSerializer(serializers.ModelSerializer):
    """
    Serializer for KYC submission.
    
    Handles validation and submission of KYC information with documents.
    """
    
    id_document = serializers.FileField(
        required=False,
        help_text='ID document (image or PDF, max 5MB)'
    )
    
    selfie = serializers.ImageField(
        required=False,
        help_text='Selfie photo (image, max 5MB)'
    )

    class Meta:
        model = KYC
        fields = [
            'id',
            'bvn',
            'nin',
            'date_of_birth',
            'address',
            'city',
            'state',
            'id_type',
            'id_number',
            'id_document',
            'selfie',
        ]
        read_only_fields = ['id']

    def validate_bvn(self, value):
        """Validate BVN format."""
        is_valid, error_message = KYCService.validate_bvn(value)
        if not is_valid:
            raise serializers.ValidationError(error_message)
        return value

    def validate_nin(self, value):
        """Validate NIN format if provided."""
        if value:
            is_valid, error_message = KYCService.validate_nin(value)
            if not is_valid:
                raise serializers.ValidationError(error_message)
        return value

    def validate_id_document(self, value):
        """Validate ID document file."""
        if value:
            # Check file size (5MB max)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError('ID document size cannot exceed 5MB')
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf']
            if value.content_type not in allowed_types:
                raise serializers.ValidationError(
                    'ID document must be an image (JPEG, PNG) or PDF file'
                )
        
        return value

    def validate_selfie(self, value):
        """Validate selfie image."""
        if value:
            # Check file size (5MB max)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError('Selfie size cannot exceed 5MB')
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/png', 'image/jpg']
            if value.content_type not in allowed_types:
                raise serializers.ValidationError('Selfie must be an image (JPEG, PNG)')
        
        return value

    def validate(self, attrs):
        """Validate that required documents are provided for Tier 1."""
        # For Tier 1, BVN is required
        if not attrs.get('bvn'):
            raise serializers.ValidationError({
                'bvn': 'BVN is required for KYC verification'
            })
        
        # ID document and selfie are required
        if not attrs.get('id_document') and not self.instance:
            raise serializers.ValidationError({
                'id_document': 'ID document is required'
            })
        
        if not attrs.get('selfie') and not self.instance:
            raise serializers.ValidationError({
                'selfie': 'Selfie is required for verification'
            })
        
        return attrs

    def create(self, validated_data):
        """Create or update KYC record."""
        user = self.context['request'].user
        
        # Extract files
        id_document = validated_data.pop('id_document', None)
        selfie = validated_data.pop('selfie', None)
        
        # Submit KYC using service
        kyc = KYCService.submit_kyc(
            user=user,
            kyc_data=validated_data,
            id_document=id_document,
            selfie=selfie
        )
        
        return kyc


class KYCStatusSerializer(serializers.ModelSerializer):
    """
    Serializer for KYC status display.
    
    Returns comprehensive KYC information including tier limits.
    """
    
    tier_name = serializers.CharField(source='get_tier_limits.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    limits = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    restrictions = serializers.SerializerMethodField()
    can_upgrade = serializers.SerializerMethodField()

    class Meta:
        model = KYC
        fields = [
            'id',
            'tier',
            'tier_name',
            'status',
            'status_display',
            'limits',
            'features',
            'restrictions',
            'submitted_at',
            'verified_at',
            'rejection_reason',
            'can_upgrade',
        ]
        read_only_fields = fields

    def get_limits(self, obj):
        """Get tier limits."""
        limits = obj.get_tier_limits()
        return {
            'daily_limit': float(limits['daily_limit']),
            'single_transaction_limit': float(limits['single_transaction_limit']),
            'total_balance_limit': float(limits['total_balance_limit']),
            'monthly_limit': float(limits['monthly_limit']),
            'daily_limit_formatted': f"₦{limits['daily_limit']:,.2f}",
            'single_transaction_limit_formatted': f"₦{limits['single_transaction_limit']:,.2f}",
            'total_balance_limit_formatted': f"₦{limits['total_balance_limit']:,.2f}",
            'monthly_limit_formatted': f"₦{limits['monthly_limit']:,.2f}",
        }

    def get_features(self, obj):
        """Get tier features."""
        limits = obj.get_tier_limits()
        return limits.get('features', [])

    def get_restrictions(self, obj):
        """Get tier restrictions."""
        limits = obj.get_tier_limits()
        return limits.get('restrictions', [])

    def get_can_upgrade(self, obj):
        """Check if user can upgrade to next tier."""
        from .tier_limits import can_upgrade_tier, get_next_tier_requirements
        
        if can_upgrade_tier(obj.tier):
            next_tier = get_next_tier_requirements(obj.tier)
            return {
                'can_upgrade': True,
                'next_tier': next_tier,
            }
        
        return {
            'can_upgrade': False,
            'next_tier': None,
        }


class KYCDocumentSerializer(serializers.ModelSerializer):
    """Serializer for additional KYC documents."""
    
    class Meta:
        model = KYCDocument
        fields = [
            'id',
            'document_type',
            'document',
            'notes',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def validate_document(self, value):
        """Validate document file."""
        # Check file size (5MB max)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError('Document size cannot exceed 5MB')
        
        return value


class KYCDetailSerializer(serializers.ModelSerializer):
    """
    Detailed KYC serializer with all information.
    
    Used for admin/review purposes.
    """
    
    tier_name = serializers.CharField(source='get_tier_limits.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    id_type_display = serializers.CharField(source='get_id_type_display', read_only=True)
    verified_by_email = serializers.CharField(source='verified_by.email', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    additional_documents = KYCDocumentSerializer(many=True, read_only=True)
    limits = serializers.SerializerMethodField()

    class Meta:
        model = KYC
        fields = [
            'id',
            'user_email',
            'user_name',
            'tier',
            'tier_name',
            'status',
            'status_display',
            'bvn',
            'nin',
            'date_of_birth',
            'address',
            'city',
            'state',
            'id_type',
            'id_type_display',
            'id_number',
            'id_document',
            'selfie',
            'verified_by_email',
            'verified_at',
            'rejection_reason',
            'submitted_at',
            'limits',
            'additional_documents',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_limits(self, obj):
        """Get tier limits."""
        limits = obj.get_tier_limits()
        return {
            'daily_limit': float(limits['daily_limit']),
            'single_transaction_limit': float(limits['single_transaction_limit']),
            'total_balance_limit': float(limits['total_balance_limit']),
            'monthly_limit': float(limits['monthly_limit']),
        }
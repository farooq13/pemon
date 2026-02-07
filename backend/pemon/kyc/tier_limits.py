from decimal import Decimal

# Transaction limits for each KYC tier (in Nigerian Naira)
TIER_LIMITS = {
    0: {  # Tier 0 - Unverified
        'name': 'Unverified',
        'daily_limit': Decimal('0'),
        'single_transaction_limit': Decimal('0'),
        'total_balance_limit': Decimal('0'),
        'monthly_limit': Decimal('0'),
        'description': 'Account not verified. Please complete KYC to start transacting.',
        'features': [
            'View account details',
            'Access customer support',
        ],
        'restrictions': [
            'Cannot send money',
            'Cannot receive money',
            'Cannot pay bills',
        ],
    },
    
    1: {  # Tier 1 - Basic KYC
        'name': 'Basic KYC',
        'daily_limit': Decimal('50000.00'),  # ₦50,000 per day
        'single_transaction_limit': Decimal('10000.00'),  # ₦10,000 per transaction
        'total_balance_limit': Decimal('100000.00'),  # ₦100,000 total balance
        'monthly_limit': Decimal('500000.00'),  # ₦500,000 per month
        'description': 'Basic verification completed. Suitable for personal daily transactions.',
        'required_documents': [
            'BVN (Bank Verification Number)',
            'Phone number verification',
            'Email verification',
        ],
        'features': [
            'Send and receive money',
            'Pay bills (airtime, data, electricity)',
            'Save money',
            'View transaction history',
        ],
        'restrictions': [
            'Limited to ₦10,000 per transaction',
            'Maximum wallet balance: ₦100,000',
            'Cannot use merchant features',
        ],
    },
    
    2: {  # Tier 2 - Intermediate KYC
        'name': 'Intermediate KYC',
        'daily_limit': Decimal('200000.00'),  # ₦200,000 per day
        'single_transaction_limit': Decimal('50000.00'),  # ₦50,000 per transaction
        'total_balance_limit': Decimal('500000.00'),  # ₦500,000 total balance
        'monthly_limit': Decimal('2000000.00'),  # ₦2,000,000 per month
        'description': 'Enhanced verification. Suitable for regular business transactions.',
        'required_documents': [
            'All Tier 1 requirements',
            'Valid government-issued ID',
            'Selfie verification',
            'Proof of address',
        ],
        'features': [
            'All Tier 1 features',
            'Higher transaction limits',
            'Access to savings plans',
            'Basic merchant features',
            'International transfers (limited)',
        ],
        'restrictions': [
            'Limited to ₦50,000 per transaction',
            'Maximum wallet balance: ₦500,000',
        ],
    },
    
    3: {  # Tier 3 - Full KYC
        'name': 'Full KYC',
        'daily_limit': Decimal('1000000.00'),  # ₦1,000,000 per day
        'single_transaction_limit': Decimal('200000.00'),  # ₦200,000 per transaction
        'total_balance_limit': Decimal('5000000.00'),  # ₦5,000,000 total balance
        'monthly_limit': Decimal('10000000.00'),  # ₦10,000,000 per month
        'description': 'Full verification completed. No restrictions on standard transactions.',
        'required_documents': [
            'All Tier 2 requirements',
            'NIN (National Identification Number)',
            'Utility bill (not older than 3 months)',
            'Bank statement (optional)',
            'Enhanced due diligence documents',
        ],
        'features': [
            'All Tier 2 features',
            'Highest transaction limits',
            'Full merchant features',
            'Payment links and QR codes',
            'Business accounts',
            'International transfers (full)',
            'Agent capabilities',
            'API access',
        ],
        'restrictions': [
            'May require periodic re-verification',
        ],
    },
}


def get_tier_name(tier_level):
    """
    Get the name of a KYC tier.
    
    """
    return TIER_LIMITS.get(tier_level, {}).get('name', 'Unknown')


def get_tier_description(tier_level):
    """
    Get the description of a KYC tier.
    
    """
    return TIER_LIMITS.get(tier_level, {}).get('description', '')


def get_next_tier_requirements(current_tier):
    """
    Get requirements to upgrade to the next tier.
    
    """
    next_tier = current_tier + 1
    
    if next_tier > 3:
        return None
    
    tier_info = TIER_LIMITS.get(next_tier, {})
    
    return {
        'tier': next_tier,
        'name': tier_info.get('name'),
        'description': tier_info.get('description'),
        'required_documents': tier_info.get('required_documents', []),
        'features': tier_info.get('features', []),
        'daily_limit': tier_info.get('daily_limit'),
        'single_transaction_limit': tier_info.get('single_transaction_limit'),
        'total_balance_limit': tier_info.get('total_balance_limit'),
    }


def can_upgrade_tier(current_tier):
    """
    Check if user can upgrade to next tier.
    
    """
    return current_tier < 3


def format_limit(amount):
    """
    Format amount as Nigerian currency.
    
    """
    if amount == 0:
        return '₦0.00'
    return f'₦{amount:,.2f}'


def get_tier_comparison():
    """
    Get comparison of all tiers for display purposes.
    
    Returns:
        list: List of tier information dictionaries
    """
    comparison = []
    
    for tier_level in range(4):
        tier_info = TIER_LIMITS.get(tier_level, {})
        comparison.append({
            'tier': tier_level,
            'name': tier_info.get('name'),
            'daily_limit_formatted': format_limit(tier_info.get('daily_limit', 0)),
            'single_transaction_limit_formatted': format_limit(tier_info.get('single_transaction_limit', 0)),
            'total_balance_limit_formatted': format_limit(tier_info.get('total_balance_limit', 0)),
            'features': tier_info.get('features', []),
            'restrictions': tier_info.get('restrictions', []),
        })
    
    return comparison
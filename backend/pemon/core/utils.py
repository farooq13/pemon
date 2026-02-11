"""
Utility functions for Pemon.

This module contains reusable helper functions for:
- Data formatting and validation
- Reference number generation
- Phone number handling
- Date/time utilities
- Encryption/decryption helpers
"""

import random
import re
import string
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Tuple

from django.utils import timezone


# REFERENCE NUMBER GENERATION
def generate_reference(prefix: str = 'TXN', length: int = 12) -> str:
    """
    Generate a unique reference number for transactions.
    
    Format: PREFIX-YYYYMMDD-RANDOMCHARS
    Example: TXN-20240118-ABC123XYZ
    
    Args:
        prefix (str): Prefix for the reference (e.g., 'TXN', 'PAY', 'WTH')
        length (int): Length of the random portion (default: 12)
        
    Returns:
        str: Unique reference number
        
    Example:
        >>> generate_reference('TXN', 10)
        'TXN-20240118-A1B2C3D4E5'
    """
    date_str = datetime.now().strftime('%Y%m%d')
    random_str = ''.join(
        random.choices(string.ascii_uppercase + string.digits, k=length)
    )
    return f"{prefix}-{date_str}-{random_str}"


def generate_virtual_account_number() -> str:
    """
    Generate a virtual account number for user wallets.
    
    Returns a 10-digit number starting with '2' (Nigerian bank standard).
    
    Returns:
        str: 10-digit virtual account number
        
    Example:
        >>> generate_virtual_account_number()
        '2012345678'
    """
    # Start with '2' and generate 9 random digits
    return '2' + ''.join(random.choices(string.digits, k=9))


def generate_otp(length: int = 6) -> str:
    """
    Generate a numeric OTP (One-Time Password).
    
    Args:
        length (int): Length of the OTP (default: 6)
        
    Returns:
        str: Numeric OTP
        
    Example:
        >>> generate_otp(6)
        '123456'
    """
    return ''.join(random.choices(string.digits, k=length))


# PHONE NUMBER UTILITIES
def normalize_phone_number(phone: str) -> str:
    """
    Normalize phone number to E.164 format for Nigeria.
    
    Converts various Nigerian phone formats to standard international format.
    - Removes spaces, dashes, parentheses
    - Adds +234 country code if missing
    - Removes leading 0 if present
    
    Args:
        phone (str): Phone number in any format
        
    Returns:
        str: Normalized phone number in E.164 format (+234XXXXXXXXXX)
        
    Raises:
        ValueError: If phone number is invalid
        
    Example:
        >>> normalize_phone_number('08012345678')
        '+2348012345678'
        >>> normalize_phone_number('2348012345678')
        '+2348012345678'
        >>> normalize_phone_number('+234 801 234 5678')
        '+2348012345678'
    """
    # Remove all non-digit characters
    phone = re.sub(r'\D', '', phone)
    
    # Remove leading zeros
    phone = phone.lstrip('0')
    
    # Add country code if not present
    if not phone.startswith('234'):
        phone = '234' + phone
    
    # Validate length (234 + 10 digits = 13)
    if len(phone) != 13:
        raise ValueError('Invalid Nigerian phone number')
    
    return f'+{phone}'


def detect_network_provider(phone: str) -> Optional[str]:
    """
    Detect Nigerian mobile network provider from phone number.
    """
    try:
        normalized = normalize_phone_number(phone)
        # Extract the first 4 digits after country code
        prefix = normalized[4:7]  # +234XXX
        
        # MTN prefixes
        mtn_prefixes = ['803', '806', '703', '706', '813', '816', '810', '814', '903', '906', '913']
        # Airtel prefixes
        airtel_prefixes = ['802', '808', '708', '812', '701', '902', '907', '901', '904', '912']
        # Glo prefixes
        glo_prefixes = ['805', '807', '705', '815', '811', '905', '915']
        # 9mobile prefixes
        ninemobile_prefixes = ['809', '817', '818', '909', '908']
        
        if prefix in mtn_prefixes:
            return 'MTN'
        elif prefix in airtel_prefixes:
            return 'AIRTEL'
        elif prefix in glo_prefixes:
            return 'GLO'
        elif prefix in ninemobile_prefixes:
            return '9MOBILE'
        
        return None
    except ValueError:
        return None


def validate_nigerian_phone(phone: str) -> Tuple[bool, str]:
    """
    Validate Nigerian phone number.
    
    Args:
        phone (str): Phone number to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
        
    Example:
        >>> validate_nigerian_phone('08012345678')
        (True, '')
        >>> validate_nigerian_phone('1234567')
        (False, 'Invalid phone number format')
    """
    try:
        normalized = normalize_phone_number(phone)
        return (True, '')
    except ValueError as e:
        return (False, str(e))


# MONEY FORMATTING UTILITIES
def format_money(amount: Decimal, currency: str = 'NGN') -> str:
    """
    Format money amount with currency symbol and thousand separators.
    
    Args:
        amount (Decimal): Amount to format
        currency (str): Currency code (default: 'NGN')
        
    Returns:
        str: Formatted money string
        
    Example:
        >>> format_money(Decimal('1000.50'))
        '₦1,000.50'
        >>> format_money(Decimal('1234567.89'))
        '₦1,234,567.89'
    """
    currency_symbols = {
        'NGN': '₦',
        'USD': '$',
        'GBP': '£',
        'EUR': '€',
    }
    
    symbol = currency_symbols.get(currency, currency)
    return f"{symbol}{amount:,.2f}"


def parse_money(amount_str: str) -> Decimal:
    """
    Parse money string to Decimal, removing currency symbols and commas.
    
    Args:
        amount_str (str): Money string (e.g., '₦1,000.50' or '1000.50')
        
    Returns:
        Decimal: Parsed amount
        
    Example:
        >>> parse_money('₦1,000.50')
        Decimal('1000.50')
        >>> parse_money('1,234,567.89')
        Decimal('1234567.89')
    """
    # Remove currency symbols and commas
    cleaned = re.sub(r'[₦$£€,\s]', '', amount_str)
    return Decimal(cleaned)


def validate_amount(amount: Decimal, min_amount: Decimal = Decimal('100.00'),
                   max_amount: Optional[Decimal] = None) -> Tuple[bool, str]:
    if amount <= 0:
        return (False, 'Amount must be greater than zero')
    
    if amount < min_amount:
        return (False, f'Amount must be at least {format_money(min_amount)}')
    
    if max_amount and amount > max_amount:
        return (False, f'Amount cannot exceed {format_money(max_amount)}')
    
    # Check for too many decimal places (max 2 for money)
    if amount.as_tuple().exponent < -2:
        return (False, 'Amount cannot have more than 2 decimal places')
    
    return (True, '')


# DATE/TIME UTILITIES
def get_date_range(period: str) -> Tuple[datetime, datetime]:
    now = timezone.now()
    
    if period == 'today':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == 'yesterday':
        yesterday = now - timedelta(days=1)
        start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif period == 'this_week':
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == 'this_month':
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == 'last_month':
        first_day_this_month = now.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        start = last_day_last_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = last_day_last_month.replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        raise ValueError(f'Invalid period: {period}')
    
    return (start, end)


def format_datetime(dt: datetime, format_type: str = 'full') -> str:
    if format_type == 'full':
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    elif format_type == 'date':
        return dt.strftime('%Y-%m-%d')
    elif format_type == 'time':
        return dt.strftime('%H:%M:%S')
    elif format_type == 'short':
        return dt.strftime('%d %b %Y, %I:%M %p')
    else:
        return str(dt)


# VALIDATION UTILITIES
def validate_email(email: str) -> Tuple[bool, str]:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return (False, 'Invalid email format')
    
    return (True, '')


def validate_bvn(bvn: str) -> Tuple[bool, str]:
    # Remove any spaces
    bvn = bvn.strip()
    
    # Check if it's 11 digits
    if not re.match(r'^\d{11}$', bvn):
        return (False, 'BVN must be exactly 11 digits')
    
    return (True, '')


def validate_nin(nin: str) -> Tuple[bool, str]:
    # Remove any spaces
    nin = nin.strip()
    
    # Check if it's 11 digits
    if not re.match(r'^\d{11}$', nin):
        return (False, 'NIN must be exactly 11 digits')
    
    return (True, '')


# PAGINATION UTILITIES
def get_pagination_metadata(paginator, page) -> dict:
    return {
        'current_page': page.number,
        'total_pages': paginator.num_pages,
        'page_size': paginator.per_page,
        'total_items': paginator.count,
        'has_next': page.has_next(),
        'has_previous': page.has_previous(),
        'next_page': page.next_page_number() if page.has_next() else None,
        'previous_page': page.previous_page_number() if page.has_previous() else None,
    }
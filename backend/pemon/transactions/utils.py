import random
import string
from datetime import datetime
from typing import Optional


def generate_transaction_reference(prefix: str = "TXN") -> str:
    """
    Generate a unique transaction reference.
    
    Format: PREFIX-YYYYMMDDHHMMSS-RANDOM6
    Example: TXN-20250208143022-A3B4C5
    
    Args:
        prefix: Reference prefix (default: "TXN")
        
    Returns:
        str: Unique transaction reference
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    return f"{prefix}-{timestamp}-{random_str}"


def generate_idempotency_key(
    user_id: str,
    transaction_type: str,
    amount: str,
    recipient_id: Optional[str] = None
) -> str:
    """
    Generate an idempotency key for duplicate prevention.
    
    The key is based on user, type, amount, and recipient to allow
    the same user to make multiple identical transactions if they want,
    but prevent accidental duplicates within a short time window.
    
    Args:
        user_id: User ID
        transaction_type: Transaction type
        amount: Transaction amount
        recipient_id: Recipient ID (for transfers)
        
    Returns:
        str: Idempotency key
    """
    import hashlib
    
    # Include timestamp with minute precision to allow same transaction
    # but prevent duplicates within 1 minute
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    
    components = [
        str(user_id),
        transaction_type,
        str(amount),
        str(recipient_id) if recipient_id else "NONE",
        timestamp
    ]
    
    key_string = "|".join(components)
    
    return hashlib.sha256(key_string.encode()).hexdigest()


def format_currency(amount) -> str:
    """
    Format amount as Nigerian Naira currency.
    
    Args:
        amount: Numeric amount
        
    Returns:
        str: Formatted currency string
    """
    from decimal import Decimal
    
    if isinstance(amount, str):
        amount = Decimal(amount)
    
    return f"₦{amount:,.2f}"


def parse_currency(formatted_amount: str):
    """
    Parse formatted currency string to Decimal.
    
    Args:
        formatted_amount: Formatted currency string
        
    Returns:
        Decimal: Numeric amount
    """
    from decimal import Decimal
    
    # Remove currency symbol and commas
    numeric_str = formatted_amount.replace('₦', '').replace(',', '').strip()
    
    return Decimal(numeric_str)


def validate_transaction_amount(amount, min_amount=None, max_amount=None) -> tuple:
    """
    Validate transaction amount against min/max constraints.
    
    Args:
        amount: Amount to validate
        min_amount: Minimum allowed amount
        max_amount: Maximum allowed amount
        
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    from decimal import Decimal
    
    # Convert to Decimal if string
    if isinstance(amount, str):
        try:
            amount = Decimal(amount)
        except:
            return False, "Invalid amount format"
    
    # Check if positive
    if amount <= 0:
        return False, "Amount must be greater than zero"
    
    # Check minimum
    if min_amount and amount < Decimal(str(min_amount)):
        return False, f"Amount must be at least {format_currency(min_amount)}"
    
    # Check maximum
    if max_amount and amount > Decimal(str(max_amount)):
        return False, f"Amount cannot exceed {format_currency(max_amount)}"
    
    return True, None


def calculate_fee(amount, percentage=0, fixed_fee=0):
    """
    Calculate transaction fee.
    
    Args:
        amount: Transaction amount
        percentage: Percentage fee (e.g., 1.5 for 1.5%)
        fixed_fee: Fixed fee amount
        
    Returns:
        Decimal: Calculated fee
    """
    from decimal import Decimal
    
    amount = Decimal(str(amount))
    percentage = Decimal(str(percentage))
    fixed_fee = Decimal(str(fixed_fee))
    
    percentage_fee = (amount * percentage) / Decimal('100')
    total_fee = percentage_fee + fixed_fee
    
    # Round to 2 decimal places
    return total_fee.quantize(Decimal('0.01'))


# def is_business_hours() -> bool:
#     """
#     Check if current time is within business hours.
    
#     Business hours: Monday-Friday, 8 AM - 6 PM (WAT)
    
#     Returns:
#         bool: True if within business hours
#     """
#     now = datetime.now()
    
#     # Check if weekend
#     if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
#         return False
    
#     # Check time
#     hour = now.hour
#     if hour < 8 or hour >= 18:
#         return False
    
#     return True


def mask_account_number(account_number: str) -> str:
    """
    Mask account number for security.
    
    Shows only last 4 digits.
    Example: "1234567890" -> "******7890"
    
    Args:
        account_number: Full account number
        
    Returns:
        str: Masked account number
    """
    if not account_number or len(account_number) < 4:
        return "****"
    
    masked_part = "*" * (len(account_number) - 4)
    visible_part = account_number[-4:]
    
    return masked_part + visible_part


def get_transaction_description(transaction_type: str, **kwargs) -> str:
    """
    Generate a descriptive message for a transaction.
    
    Args:
        transaction_type: Type of transaction
        **kwargs: Additional context (recipient, biller, etc.)
        
    Returns:
        str: Transaction description
    """
    descriptions = {
        'DEPOSIT': 'Wallet top-up',
        'WITHDRAWAL': 'Cash withdrawal',
        'TRANSFER': f"Transfer to {kwargs.get('recipient', 'user')}",
        'BILL_PAYMENT': f"Bill payment - {kwargs.get('biller', 'service')}",
        'AIRTIME': f"Airtime purchase - {kwargs.get('phone', 'number')}",
        'DATA': f"Data bundle - {kwargs.get('phone', 'number')}",
        'ELECTRICITY': f"Electricity - {kwargs.get('meter', 'meter')}",
        'CABLE_TV': f"Cable TV - {kwargs.get('smartcard', 'subscription')}",
        'REVERSAL': 'Transaction reversal',
        'REFUND': 'Refund',
        'COMMISSION': 'Commission earned',
        'CHARGE': 'Service charge',
    }
    
    return descriptions.get(transaction_type, 'Transaction')
"""
Custom exception handlers and exception classes for Pemon.

This module provides:
- Custom exception classes for business logic errors
- Custom DRF exception handler for consistent error responses
- Error codes and messages
"""

import logging
from typing import Any, Dict, Optional

from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


# CUSTOM EXCEPTION CLASSES
class PemonBaseException(APIException):
    """
    Base exception class for all Pemon-specific exceptions.
    
    All custom exceptions should inherit from this class for consistency.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'An error occurred.'
    default_code = 'error'


class InsufficientBalanceError(PemonBaseException):
    """
    Raised when a user attempts a transaction with insufficient wallet balance.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Insufficient wallet balance for this transaction.'
    default_code = 'insufficient_balance'


class KYCLimitExceededError(PemonBaseException):
    """
    Raised when a transaction exceeds KYC tier limits.
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Transaction exceeds your KYC tier limits. Please upgrade your verification level.'
    default_code = 'kyc_limit_exceeded'


class AccountFrozenError(PemonBaseException):
    """
    Raised when attempting operations on a frozen account/wallet.
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'This account is frozen. Please contact support.'
    default_code = 'account_frozen'


class DuplicateTransactionError(PemonBaseException):
    """
    Raised when a duplicate transaction is detected (idempotency check).
    """
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'A transaction with this reference already exists.'
    default_code = 'duplicate_transaction'


class InvalidRecipientError(PemonBaseException):
    """
    Raised when the specified recipient is not found or invalid.
    """
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Recipient not found or invalid.'
    default_code = 'invalid_recipient'


class TransactionFailedError(PemonBaseException):
    """
    Raised when a transaction processing fails.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Transaction processing failed. Please try again.'
    default_code = 'transaction_failed'


class KYCNotApprovedError(PemonBaseException):
    """
    Raised when attempting operations that require KYC approval.
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Your KYC verification is not approved. Please complete verification first.'
    default_code = 'kyc_not_approved'


class InvalidPINError(PemonBaseException):
    """
    Raised when an invalid transaction PIN is provided.
    """
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Invalid transaction PIN.'
    default_code = 'invalid_pin'


class RateLimitExceededError(PemonBaseException):
    """
    Raised when API rate limit is exceeded.
    """
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = 'Too many requests. Please try again later.'
    default_code = 'rate_limit_exceeded'


class ServiceUnavailableError(PemonBaseException):
    """
    Raised when an external service (bill payment provider, etc.) is unavailable.
    """
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Service temporarily unavailable. Please try again later.'
    default_code = 'service_unavailable'


# CUSTOM EXCEPTION HANDLER
def custom_exception_handler(exc: Exception, context: Dict[str, Any]) -> Optional[Response]:
    """
    Custom exception handler for Django REST Framework.
    
    This handler provides consistent error response format across the entire API:
    {
        "error": {
            "code": "error_code",
            "message": "Human-readable error message",
            "details": {...},  # Optional additional details
            "field_errors": {...}  # Optional field-specific errors
        }
    }
    
    Args:
        exc (Exception): The exception that was raised
        context (Dict): Context information about the request
        
    Returns:
        Response: Formatted error response or None
    """
    
    # Call DRF's default exception handler first to get the standard error response
    response = drf_exception_handler(exc, context)
    
    if response is not None:
        # Customize the error response format
        error_data = {
            'error': {
                'code': getattr(exc, 'default_code', 'error'),
                'message': str(exc),
            }
        }
        
        # Add field-specific errors if they exist
        if isinstance(response.data, dict):
            # Check for field errors (validation errors)
            if 'detail' not in response.data:
                error_data['error']['field_errors'] = response.data
            else:
                # For non-field errors, use the detail message
                if isinstance(response.data.get('detail'), str):
                    error_data['error']['message'] = response.data['detail']
                elif isinstance(response.data.get('detail'), list):
                    error_data['error']['message'] = '; '.join(response.data['detail'])
        
        response.data = error_data
        
        # Log the error
        log_exception(exc, context, response.status_code)
        
    else:
        # Handle exceptions that DRF doesn't handle by default
        if isinstance(exc, ValidationError):
            response = handle_validation_error(exc)
        elif isinstance(exc, PermissionDenied):
            response = handle_permission_denied(exc)
        elif isinstance(exc, Http404):
            response = handle_not_found(exc)
        else:
            # For unexpected errors, return 500
            response = handle_server_error(exc)
        
        # Log the error
        log_exception(exc, context, response.status_code)
    
    return response


def handle_validation_error(exc: ValidationError) -> Response:
    """Handle Django ValidationError."""
    error_data = {
        'error': {
            'code': 'validation_error',
            'message': 'Validation failed.',
            'details': exc.message_dict if hasattr(exc, 'message_dict') else {'detail': exc.messages},
        }
    }
    return Response(error_data, status=status.HTTP_400_BAD_REQUEST)


def handle_permission_denied(exc: PermissionDenied) -> Response:
    """Handle Django PermissionDenied."""
    error_data = {
        'error': {
            'code': 'permission_denied',
            'message': str(exc) or 'You do not have permission to perform this action.',
        }
    }
    return Response(error_data, status=status.HTTP_403_FORBIDDEN)


def handle_not_found(exc: Http404) -> Response:
    """Handle Django Http404."""
    error_data = {
        'error': {
            'code': 'not_found',
            'message': str(exc) or 'Resource not found.',
        }
    }
    return Response(error_data, status=status.HTTP_404_NOT_FOUND)


def handle_server_error(exc: Exception) -> Response:
    """Handle unexpected server errors."""
    error_data = {
        'error': {
            'code': 'internal_server_error',
            'message': 'An unexpected error occurred. Please try again later.',
        }
    }
    
    # Log the full exception for debugging
    logger.error(f'Unexpected error: {exc}', exc_info=True)
    
    return Response(error_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def log_exception(exc: Exception, context: Dict[str, Any], status_code: int) -> None:
    """
    Log exception details for monitoring and debugging.
    
    Args:
        exc: The exception that was raised
        context: Request context
        status_code: HTTP status code of the response
    """
    request = context.get('request')
    
    # Determine log level based on status code
    if status_code >= 500:
        log_level = logging.ERROR
    elif status_code >= 400:
        log_level = logging.WARNING
    else:
        log_level = logging.INFO
    
    # Log the exception
    logger.log(
        log_level,
        f'{exc.__class__.__name__}: {str(exc)}',
        extra={
            'status_code': status_code,
            'path': request.path if request else None,
            'method': request.method if request else None,
            'user': str(request.user) if request and hasattr(request, 'user') else None,
        },
        exc_info=status_code >= 500  # Include traceback for 500 errors
    )


# ERROR CODE CONSTANTS
class ErrorCodes:
    """Centralized error code constants for consistent error handling."""
    
    # Authentication & Authorization
    INVALID_CREDENTIALS = 'invalid_credentials'
    TOKEN_EXPIRED = 'token_expired'
    TOKEN_INVALID = 'token_invalid'
    PERMISSION_DENIED = 'permission_denied'
    ACCOUNT_DISABLED = 'account_disabled'
    
    # Validation
    VALIDATION_ERROR = 'validation_error'
    INVALID_INPUT = 'invalid_input'
    MISSING_FIELD = 'missing_field'
    
    # Resources
    NOT_FOUND = 'not_found'
    ALREADY_EXISTS = 'already_exists'
    DUPLICATE_ENTRY = 'duplicate_entry'
    
    # Transactions
    INSUFFICIENT_BALANCE = 'insufficient_balance'
    TRANSACTION_FAILED = 'transaction_failed'
    DUPLICATE_TRANSACTION = 'duplicate_transaction'
    INVALID_AMOUNT = 'invalid_amount'
    
    # KYC
    KYC_NOT_APPROVED = 'kyc_not_approved'
    KYC_LIMIT_EXCEEDED = 'kyc_limit_exceeded'
    INVALID_KYC_DOCUMENT = 'invalid_kyc_document'
    
    # Account
    ACCOUNT_FROZEN = 'account_frozen'
    WALLET_FROZEN = 'wallet_frozen'
    INVALID_PIN = 'invalid_pin'
    
    # System
    INTERNAL_ERROR = 'internal_server_error'
    SERVICE_UNAVAILABLE = 'service_unavailable'
    RATE_LIMIT_EXCEEDED = 'rate_limit_exceeded'
    MAINTENANCE_MODE = 'maintenance_mode'
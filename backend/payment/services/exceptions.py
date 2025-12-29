"""
Payment Service Exceptions
"""
from django.core.exceptions import ValidationError


class PaymentException(Exception):
    """Base exception for payment operations"""
    pass


class DuplicateTransactionError(PaymentException):
    """Raised when duplicate transaction is detected"""
    pass


class InvalidTransactionError(PaymentException, ValidationError):
    """Raised when transaction data is invalid"""
    pass


class GatewayError(PaymentException):
    """Raised when gateway operation fails"""
    pass


class VerificationError(PaymentException):
    """Raised when payment verification fails"""
    pass


"""
Custom API Exception Handlers
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from payment.services.exceptions import (
    PaymentException,
    DuplicateTransactionError,
    InvalidTransactionError,
    GatewayError,
    VerificationError
)
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for payment API.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Handle custom payment exceptions
    if isinstance(exc, DuplicateTransactionError):
        return Response(
            {
                'error': 'duplicate_transaction',
                'message': str(exc),
                'detail': 'This transaction has already been processed'
            },
            status=status.HTTP_409_CONFLICT
        )
    
    if isinstance(exc, InvalidTransactionError):
        return Response(
            {
                'error': 'invalid_transaction',
                'message': str(exc),
                'detail': 'Transaction data is invalid'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if isinstance(exc, GatewayError):
        return Response(
            {
                'error': 'gateway_error',
                'message': str(exc),
                'detail': 'Payment gateway operation failed'
            },
            status=status.HTTP_502_BAD_GATEWAY
        )
    
    if isinstance(exc, VerificationError):
        return Response(
            {
                'error': 'verification_error',
                'message': str(exc),
                'detail': 'Payment verification failed'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if isinstance(exc, PaymentException):
        return Response(
            {
                'error': 'payment_error',
                'message': str(exc),
                'detail': 'Payment operation failed'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Return default response if not handled
    return response


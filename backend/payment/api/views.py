"""
DRF Views for Payment API
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from payment.services.transaction_service import TransactionService
from payment.services.exceptions import PaymentException
from payment.verification import ZarinpalVerifier, StripeVerifier, PayPalVerifier
from payment.models import GatewayType
from .serializers import (
    PaymentInitializeSerializer,
    PaymentInitializeResponseSerializer,
    PaymentVerifySerializer,
    PaymentVerifyResponseSerializer,
    PaymentStatusSerializer
)

logger = logging.getLogger(__name__)

# Service instances
transaction_service = TransactionService()
verifiers = {
    GatewayType.ZARINPAL: ZarinpalVerifier(),
    GatewayType.STRIPE: StripeVerifier(),
    GatewayType.PAYPAL: PayPalVerifier(),
}


@swagger_auto_schema(
    method='post',
    request_body=PaymentInitializeSerializer,
    responses={
        201: PaymentInitializeResponseSerializer,
        400: 'Bad Request',
        409: 'Duplicate Transaction',
        502: 'Gateway Error'
    },
    operation_summary="Initialize Payment",
    operation_description="Create a new payment transaction and get redirect URL"
)
@api_view(['POST'])
@permission_classes([AllowAny])
def initialize_payment(request):
    """
    Initialize a new payment transaction.
    
    POST /api/v1/payments/initialize/
    
    Body:
    {
        "amount": 150000,
        "currency": "IRR",
        "gateway": 1,
        "order_id": "1234-567",
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "description": "Payment for order",
        "callback_url": "https://example.com/callback",
        "idempotency_key": "optional-key",
        "metadata": {}
    }
    """
    serializer = PaymentInitializeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        result = transaction_service.create_payment(
            order_id=serializer.validated_data['order_id'],
            user_id=str(serializer.validated_data['user_id']),
            gateway_id=serializer.validated_data['gateway'],
            amount=serializer.validated_data['amount'],
            currency=serializer.validated_data.get('currency', 'IRR'),
            description=serializer.validated_data.get('description', ''),
            callback_url=serializer.validated_data.get('callback_url'),
            idempotency_key=serializer.validated_data.get('idempotency_key'),
            metadata=serializer.validated_data.get('metadata', {})
        )
        
        response_serializer = PaymentInitializeResponseSerializer(result)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
    except PaymentException as e:
        logger.error(f"Payment initialization failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in payment initialization: {e}", exc_info=True)
        return Response(
            {'error': 'internal_error', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='post',
    request_body=PaymentVerifySerializer,
    responses={
        200: PaymentVerifyResponseSerializer,
        400: 'Bad Request',
        404: 'Transaction Not Found'
    },
    operation_summary="Verify Payment",
    operation_description="Verify a payment transaction after gateway callback"
)
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_payment(request):
    """
    Verify a payment transaction.
    
    POST /api/v1/payments/verify/
    
    Body:
    {
        "payment_id": "550e8400-e29b-41d4-a716-446655440000",
        "callback_data": {
            "Authority": "A00000000000000000000000000000000000000",
            "Status": "OK"
        },
        "idempotency_key": "optional-key"
    }
    """
    serializer = PaymentVerifySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    payment_id = str(serializer.validated_data['payment_id'])
    callback_data = serializer.validated_data['callback_data']
    idempotency_key = serializer.validated_data.get('idempotency_key')
    
    try:
        # Get transaction to determine gateway
        transaction = transaction_service.get_transaction_status(payment_id)
        gateway_id = transaction.gateway_id
        
        # Get appropriate verifier
        gateway_type = GatewayType(gateway_id)
        verifier = verifiers.get(gateway_type)
        
        if not verifier:
            return Response(
                {'error': 'gateway_not_supported', 'message': f'Gateway {gateway_id} not supported'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify payment
        result = verifier.verify(payment_id, callback_data, idempotency_key=idempotency_key)
        
        response_serializer = PaymentVerifyResponseSerializer(result)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
        
    except PaymentException as e:
        logger.error(f"Payment verification failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in payment verification: {e}", exc_info=True)
        return Response(
            {'error': 'internal_error', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    responses={
        200: PaymentStatusSerializer,
        404: 'Transaction Not Found'
    },
    operation_summary="Get Payment Status",
    operation_description="Get the current status of a payment transaction"
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_payment_status(request, payment_id):
    """
    Get payment transaction status.
    
    GET /api/v1/payments/{payment_id}/status/
    """
    try:
        transaction = transaction_service.get_transaction_status(payment_id)
        serializer = PaymentStatusSerializer(transaction)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except PaymentException as e:
        logger.error(f"Failed to get payment status: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting payment status: {e}", exc_info=True)
        return Response(
            {'error': 'internal_error', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


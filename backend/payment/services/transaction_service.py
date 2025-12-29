"""
Transaction Service
Core business logic for payment transactions
Preserves logic from app/transacion/handler.py and app/services/manager.py
"""
import logging
import uuid
from typing import Dict, Any, Optional, Tuple
from django.db import transaction as db_transaction
from django.conf import settings
from payment.models import Transaction, TransactionEvent, GatewayType
from payment.gateways import ZarinpalGateway, StripeGateway, PayPalGateway
from payment.utils.redis_client import redis_client
from payment.utils.hashing import generate_idempotency_key
from .idempotency_manager import IdempotencyManager
from .exceptions import PaymentException, InvalidTransactionError, GatewayError

logger = logging.getLogger(__name__)


class TransactionService:
    """
    Service for managing payment transactions.
    Preserves business logic from existing handlers.
    """
    
    # Gateway mapping
    GATEWAY_MAP = {
        GatewayType.ZARINPAL: ZarinpalGateway,
        GatewayType.STRIPE: StripeGateway,
        GatewayType.PAYPAL: PayPalGateway,
    }
    
    def __init__(self):
        self.gateways = {
            GatewayType.ZARINPAL: ZarinpalGateway(),
            GatewayType.STRIPE: StripeGateway(),
            GatewayType.PAYPAL: PayPalGateway(),
        }
    
    def create_payment(
        self,
        order_id: str,
        user_id: str,
        gateway_id: int,
        amount: int,
        currency: str = 'IRR',
        description: str = '',
        callback_url: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new payment transaction.
        Preserves logic from app/transacion/handler.py save_transaction
        
        Args:
            order_id: Order identifier
            user_id: User UUID
            gateway_id: Gateway type ID
            amount: Transaction amount
            currency: Currency code
            description: Transaction description
            callback_url: Callback URL for gateway
            idempotency_key: Idempotency key (optional, auto-generated if not provided)
            metadata: Additional metadata
            **kwargs: Additional gateway-specific parameters
            
        Returns:
            Dict containing payment_id and redirect_url
            
        Raises:
            InvalidTransactionError: If transaction data is invalid
            DuplicateTransactionError: If duplicate transaction detected
            GatewayError: If gateway operation fails
        """
        # Validate gateway
        try:
            gateway_type = GatewayType(gateway_id)
        except ValueError:
            raise InvalidTransactionError(f"Invalid gateway_id: {gateway_id}")
        
        # Generate idempotency key if not provided
        if not idempotency_key:
            idempotency_key = generate_idempotency_key({
                'order_id': order_id,
                'amount': amount,
                'gateway_id': gateway_id
            })
        
        # Check idempotency
        IdempotencyManager.validate_and_set_idempotency(idempotency_key)
        
        # Get gateway
        gateway = self.gateways.get(gateway_type)
        if not gateway:
            raise InvalidTransactionError(f"Gateway {gateway_type} not configured")
        
        # Create payment with gateway
        gateway_response = gateway.create_payment(
            amount=amount,
            currency=currency,
            callback_url=callback_url or gateway.get_default_callback_url(),
            description=description,
            metadata=metadata or {},
            **kwargs
        )
        
        if gateway_response.get('status') != 'success':
            raise GatewayError(
                gateway_response.get('message', 'Gateway request failed'),
                error_code=gateway_response.get('error_code')
            )
        
        # Extract authority code and payment link
        gateway_data = gateway_response.get('data', {})
        authority_code = gateway_data.get('authority') or gateway_data.get('authority_code')
        payment_link = gateway_data.get('link')
        
        if not authority_code:
            raise GatewayError("Gateway did not return authority code")
        
        # Save transaction to database
        try:
            with db_transaction.atomic():
                transaction_obj = Transaction.objects.create(
                    order_id=order_id,
                    user_id=uuid.UUID(user_id) if isinstance(user_id, str) else user_id,
                    gateway_id=gateway_id,
                    amount=amount,
                    currency=currency,
                    description=description,
                    authority_code=authority_code,
                    idempotency_key=idempotency_key,
                    meta=metadata or {},
                    is_done=False,
                    is_added_wallet=False,
                    is_refund=False
                )
                
                # Cache transaction
                transaction_data = {
                    'transaction_uuid': str(transaction_obj.transaction_uuid),
                    'order_id': transaction_obj.order_id,
                    'user_id': str(transaction_obj.user_id),
                    'gateway_id': str(transaction_obj.gateway_id),
                    'amount': str(transaction_obj.amount),
                    'currency': transaction_obj.currency,
                    'description': transaction_obj.description,
                    'authority_code': transaction_obj.authority_code or '',
                    'ref_id': transaction_obj.ref_id or '',
                    'is_done': str(transaction_obj.is_done),
                    'is_added_wallet': str(transaction_obj.is_added_wallet),
                    'is_refund': str(transaction_obj.is_refund),
                }
                redis_client.cache_transaction(
                    str(transaction_obj.transaction_uuid),
                    transaction_data
                )
                
                # Set state in Redis
                redis_client.set_transaction_state(
                    str(transaction_obj.transaction_uuid),
                    'pending'
                )
                
                # Set idempotency key
                IdempotencyManager.set_idempotency_key(idempotency_key)
                
                # Log event
                TransactionEvent.objects.create(
                    transaction=transaction_obj,
                    old_status='new',
                    new_status='created',
                    event_source='payment_gateway',
                    payload={'action': 'transaction_created', 'gateway_response': gateway_response}
                )
                
                logger.info(f"Transaction created: {transaction_obj.transaction_uuid}")
                
                return {
                    'payment_id': str(transaction_obj.transaction_uuid),
                    'redirect_url': payment_link,
                    'authority_code': authority_code
                }
                
        except Exception as e:
            logger.error(f"Failed to create transaction: {e}", exc_info=True)
            raise PaymentException(f"Failed to create transaction: {str(e)}")
    
    def get_transaction_status(self, payment_id: str) -> Transaction:
        """
        Get transaction status.
        
        Args:
            payment_id: Transaction UUID
            
        Returns:
            Transaction model instance
        """
        try:
            transaction_uuid = uuid.UUID(payment_id)
        except ValueError:
            raise InvalidTransactionError(f"Invalid payment_id: {payment_id}")
        
        # Get from database
        try:
            transaction = Transaction.objects.get(transaction_uuid=transaction_uuid)
            return transaction
        except Transaction.DoesNotExist:
            raise InvalidTransactionError(f"Transaction not found: {payment_id}")


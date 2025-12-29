"""
Zarinpal Verification Handler
Preserves logic from app/verification/hamdler.py and app/verification/zarinpal_verifier.py
"""
import logging
from typing import Dict, Any
from django.db import transaction as db_transaction
from payment.models import Transaction, TransactionEvent
from payment.gateways import ZarinpalGateway
from payment.utils.redis_client import redis_client
from payment.services.idempotency_manager import IdempotencyManager
from payment.services.exceptions import VerificationError, InvalidTransactionError
from .base import BaseVerifier

logger = logging.getLogger(__name__)


class ZarinpalVerifier(BaseVerifier):
    """Zarinpal payment verification handler"""
    
    def __init__(self):
        self.gateway = ZarinpalGateway()
    
    def verify(
        self,
        transaction_uuid: str,
        callback_data: Dict[str, Any],
        idempotency_key: str = None
    ) -> Dict[str, Any]:
        """
        Verify Zarinpal payment transaction.
        Preserves logic from app/verification/hamdler.py VerifyZarinpallHandeler
        """
        try:
            # Get transaction
            try:
                transaction = Transaction.objects.get(transaction_uuid=transaction_uuid)
            except Transaction.DoesNotExist:
                raise InvalidTransactionError(f"Transaction not found: {transaction_uuid}")
            
            # Check if already verified
            if transaction.is_done:
                logger.warning(f"Transaction already verified: {transaction_uuid}")
                return {
                    'status': 'already_verified',
                    'payment_id': transaction_uuid,
                    'ref_id': transaction.ref_id,
                    'message': 'Transaction already verified'
                }
            
            # Check idempotency if provided
            if idempotency_key:
                IdempotencyManager.validate_and_set_idempotency(idempotency_key)
            
            # Get authority code
            authority_code = callback_data.get('Authority') or callback_data.get('authority') or transaction.authority_code
            if not authority_code:
                raise InvalidTransactionError("Authority code not found in callback data")
            
            # Verify with gateway
            verify_response = self.gateway.verify_payment({
                'authority': authority_code,
                'amount': transaction.amount
            })
            
            old_status = transaction.status
            
            # Process verification response
            if verify_response.get('status') == 'success' and verify_response.get('pay'):
                ref_id = verify_response.get('RefID')
                
                # Update transaction
                with db_transaction.atomic():
                    transaction.mark_as_completed(ref_id=ref_id)
                    
                    # Remove from cache
                    redis_client.remove_transaction_cache(transaction_uuid)
                    
                    # Set state
                    redis_client.set_transaction_state(transaction_uuid, 'paid')
                    
                    # Set idempotency if provided
                    if idempotency_key:
                        IdempotencyManager.set_idempotency_key(idempotency_key)
                    
                    # Log event
                    TransactionEvent.objects.create(
                        transaction=transaction,
                        old_status=old_status,
                        new_status=transaction.status,
                        event_source='payment_verification',
                        payload={
                            'action': 'payment_verified',
                            'ref_id': ref_id,
                            'gateway_response': verify_response
                        }
                    )
                
                logger.info(f"Payment verified successfully: {transaction_uuid}, RefID: {ref_id}")
                
                return {
                    'status': 'success',
                    'payment_id': transaction_uuid,
                    'ref_id': ref_id,
                    'tracking_code': ref_id,
                    'message': 'Payment verified successfully'
                }
            
            elif verify_response.get('status') == 'already_verified':
                return {
                    'status': 'already_verified',
                    'payment_id': transaction_uuid,
                    'message': verify_response.get('message', 'Payment already verified')
                }
            
            else:
                # Verification failed
                error_message = verify_response.get('message', 'Payment verification failed')
                logger.error(f"Payment verification failed: {transaction_uuid}, {error_message}")
                
                # Log event
                TransactionEvent.objects.create(
                    transaction=transaction,
                    old_status=old_status,
                    new_status='failed',
                    event_source='payment_verification',
                    payload={
                        'action': 'verification_failed',
                        'gateway_response': verify_response
                    }
                )
                
                raise VerificationError(error_message)
                
        except Exception as e:
            logger.error(f"Verification error: {e}", exc_info=True)
            raise


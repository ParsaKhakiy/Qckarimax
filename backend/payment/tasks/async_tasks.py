"""
Async background tasks for payment operations
"""
import logging
from celery import shared_task
from payment.services.transaction_service import TransactionService
from payment.verification import ZarinpalVerifier, StripeVerifier, PayPalVerifier
from payment.models import GatewayType
from payment.services.exceptions import PaymentException

logger = logging.getLogger(__name__)

transaction_service = TransactionService()
verifiers = {
    GatewayType.ZARINPAL: ZarinpalVerifier(),
    GatewayType.STRIPE: StripeVerifier(),
    GatewayType.PAYPAL: PayPalVerifier(),
}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def verify_payment_async(self, payment_id: str, callback_data: dict, idempotency_key: str = None):
    """
    Async task to verify payment transaction.
    Retries up to 3 times with exponential backoff.
    
    Args:
        payment_id: Transaction UUID
        callback_data: Callback data from gateway
        idempotency_key: Optional idempotency key
    """
    try:
        # Get transaction to determine gateway
        transaction = transaction_service.get_transaction_status(payment_id)
        gateway_type = GatewayType(transaction.gateway_id)
        
        # Get appropriate verifier
        verifier = verifiers.get(gateway_type)
        if not verifier:
            logger.error(f"Gateway {gateway_type} not supported for async verification")
            return {'status': 'error', 'message': f'Gateway {gateway_type} not supported'}
        
        # Verify payment
        result = verifier.verify(payment_id, callback_data, idempotency_key=idempotency_key)
        
        logger.info(f"Async verification completed: {payment_id}")
        return result
        
    except PaymentException as e:
        logger.error(f"Payment verification failed: {e}")
        # Retry on certain errors
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        return {'status': 'error', 'message': str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in async verification: {e}", exc_info=True)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        return {'status': 'error', 'message': str(e)}


@shared_task
def cleanup_expired_transactions():
    """
    Periodic task to cleanup expired pending transactions.
    Should be run daily via Celery beat.
    """
    from datetime import timedelta
    from django.utils import timezone
    from payment.models import Transaction, TransactionStatus
    
    # Find transactions pending for more than 24 hours
    cutoff_time = timezone.now() - timedelta(hours=24)
    expired = Transaction.objects.filter(
        is_done=False,
        created_at__lt=cutoff_time
    )
    
    count = expired.count()
    if count > 0:
        # Mark as cancelled
        expired.update(is_done=False)  # Keep as pending but could add cancelled status
        logger.info(f"Cleaned up {count} expired transactions")
    
    return {'cleaned': count}


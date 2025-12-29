"""
Idempotency Manager
Prevents duplicate transactions using Redis and Database checks
"""
import logging
from typing import Optional, Dict, Any
from django.db import transaction
from payment.models import Transaction
from payment.utils.redis_client import redis_client
from .exceptions import DuplicateTransactionError

logger = logging.getLogger(__name__)


class IdempotencyManager:
    """
    Manages idempotency checks to prevent duplicate transactions.
    Preserves logic from app/verification/hamdler.py idempotency checks
    """
    
    @staticmethod
    def check_idempotency(idempotency_key: str) -> Optional[Dict[str, Any]]:
        """
        Check if idempotency key exists (duplicate request).
        
        Args:
            idempotency_key: Idempotency key to check
            
        Returns:
            Optional[Dict]: Existing transaction data if found, None otherwise
            
        Raises:
            DuplicateTransactionError: If duplicate transaction detected
        """
        if not idempotency_key:
            return None
        
        # First check Redis cache
        if redis_client.check_idempotency(idempotency_key):
            logger.warning(f"Idempotency key found in cache: {idempotency_key}")
            # Try to get transaction from database
            try:
                existing = Transaction.objects.get(idempotency_key=idempotency_key)
                return {
                    'transaction_uuid': str(existing.transaction_uuid),
                    'order_id': existing.order_id,
                    'authority_code': existing.authority_code,
                    'is_done': existing.is_done
                }
            except Transaction.DoesNotExist:
                pass
        
        # Check database
        try:
            existing = Transaction.objects.get(idempotency_key=idempotency_key)
            logger.warning(f"Idempotency key found in database: {idempotency_key}")
            return {
                'transaction_uuid': str(existing.transaction_uuid),
                'order_id': existing.order_id,
                'authority_code': existing.authority_code,
                'is_done': existing.is_done
            }
        except Transaction.DoesNotExist:
            pass
        
        return None
    
    @staticmethod
    def set_idempotency_key(idempotency_key: str) -> bool:
        """
        Set idempotency key in cache.
        
        Args:
            idempotency_key: Idempotency key to set
            
        Returns:
            bool: True if set successfully
        """
        if not idempotency_key:
            return False
        return redis_client.set_idempotency_key(idempotency_key)
    
    @staticmethod
    def validate_and_set_idempotency(idempotency_key: str) -> str:
        """
        Validate idempotency key and raise error if duplicate.
        
        Args:
            idempotency_key: Idempotency key to validate
            
        Returns:
            str: Validated idempotency key
            
        Raises:
            DuplicateTransactionError: If duplicate detected
        """
        if not idempotency_key:
            return idempotency_key
        
        existing = IdempotencyManager.check_idempotency(idempotency_key)
        if existing:
            raise DuplicateTransactionError(
                f"Transaction with idempotency_key {idempotency_key} already exists. "
                f"Transaction UUID: {existing.get('transaction_uuid')}"
            )
        
        return idempotency_key


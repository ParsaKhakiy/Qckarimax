"""
Hashing utilities for payment security
"""
import hashlib
import hmac
from typing import Optional
from django.conf import settings


def generate_idempotency_key(data: dict) -> str:
    """
    Generate idempotency key from transaction data.
    
    Args:
        data: Transaction data dictionary
        
    Returns:
        str: Idempotency key hash
    """
    # Create a deterministic key from transaction data
    key_data = f"{data.get('order_id')}:{data.get('amount')}:{data.get('gateway_id')}"
    return hashlib.sha256(key_data.encode()).hexdigest()


def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """
    Verify webhook signature from payment gateway.
    
    Args:
        payload: Webhook payload string
        signature: Signature from gateway
        secret: Secret key for verification
        
    Returns:
        bool: True if signature is valid
    """
    try:
        expected_signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_signature, signature)
    except Exception:
        return False


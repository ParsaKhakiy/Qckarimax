"""
Redis Client Utility for Payment State Management
"""
import json
import logging
from typing import Dict, Any, Optional
from django.conf import settings
from django.core.cache import cache
import redis

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Redis client wrapper for payment state management,
    idempotency checking, and transaction caching.
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.transaction_ttl = settings.TRANSACTION_CACHE_TTL
        self.idempotency_ttl = settings.IDEMPOTENCY_CACHE_TTL
    
    def cache_transaction(self, transaction_uuid: str, transaction_data: Dict[str, Any]) -> bool:
        """
        Cache transaction data in Redis with TTL.
        
        Args:
            transaction_uuid: Transaction UUID
            transaction_data: Transaction data dictionary
            
        Returns:
            bool: True if cached successfully
        """
        try:
            cache_key = f"payment:transaction:{transaction_uuid}"
            # Convert all values to strings for Redis hash
            cache_data = {k: str(v) if not isinstance(v, str) else v 
                         for k, v in transaction_data.items()}
            self.redis_client.hset(cache_key, mapping=cache_data)
            self.redis_client.expire(cache_key, self.transaction_ttl)
            logger.info(f"Transaction cached: {transaction_uuid}")
            return True
        except Exception as e:
            logger.error(f"Failed to cache transaction {transaction_uuid}: {e}")
            return False
    
    def get_cached_transaction(self, transaction_uuid: str) -> Optional[Dict[str, Any]]:
        """
        Get cached transaction data from Redis.
        
        Args:
            transaction_uuid: Transaction UUID
            
        Returns:
            Optional[Dict]: Cached transaction data or None
        """
        try:
            cache_key = f"payment:transaction:{transaction_uuid}"
            cached_data = self.redis_client.hgetall(cache_key)
            if cached_data:
                logger.info(f"Transaction cache hit: {transaction_uuid}")
                return cached_data
            logger.debug(f"Transaction cache miss: {transaction_uuid}")
            return None
        except Exception as e:
            logger.error(f"Failed to get cached transaction {transaction_uuid}: {e}")
            return None
    
    def remove_transaction_cache(self, transaction_uuid: str) -> bool:
        """
        Remove transaction from cache.
        
        Args:
            transaction_uuid: Transaction UUID
            
        Returns:
            bool: True if removed successfully
        """
        try:
            cache_key = f"payment:transaction:{transaction_uuid}"
            result = self.redis_client.delete(cache_key)
            if result:
                logger.info(f"Transaction cache removed: {transaction_uuid}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove transaction cache {transaction_uuid}: {e}")
            return False
    
    def set_transaction_state(self, transaction_uuid: str, state: str, ttl: int = None) -> bool:
        """
        Set transaction state in Redis.
        
        Args:
            transaction_uuid: Transaction UUID
            state: State value (pending, paid, failed, etc.)
            ttl: Time to live in seconds (default: transaction_ttl)
            
        Returns:
            bool: True if set successfully
        """
        try:
            state_key = f"payment:state:{transaction_uuid}"
            ttl = ttl or self.transaction_ttl
            self.redis_client.setex(state_key, ttl, state)
            logger.debug(f"Transaction state set: {transaction_uuid} -> {state}")
            return True
        except Exception as e:
            logger.error(f"Failed to set transaction state {transaction_uuid}: {e}")
            return False
    
    def get_transaction_state(self, transaction_uuid: str) -> Optional[str]:
        """
        Get transaction state from Redis.
        
        Args:
            transaction_uuid: Transaction UUID
            
        Returns:
            Optional[str]: State value or None
        """
        try:
            state_key = f"payment:state:{transaction_uuid}"
            state = self.redis_client.get(state_key)
            return state
        except Exception as e:
            logger.error(f"Failed to get transaction state {transaction_uuid}: {e}")
            return None
    
    def check_idempotency(self, idempotency_key: str) -> bool:
        """
        Check if idempotency key exists in cache.
        
        Args:
            idempotency_key: Idempotency key
            
        Returns:
            bool: True if key exists (duplicate request)
        """
        try:
            idempotency_key_redis = f"payment:idempotency:{idempotency_key}"
            exists = self.redis_client.exists(idempotency_key_redis)
            return bool(exists)
        except Exception as e:
            logger.error(f"Failed to check idempotency key: {e}")
            return False
    
    def set_idempotency_key(self, idempotency_key: str) -> bool:
        """
        Set idempotency key in cache.
        
        Args:
            idempotency_key: Idempotency key
            
        Returns:
            bool: True if set successfully
        """
        try:
            idempotency_key_redis = f"payment:idempotency:{idempotency_key}"
            self.redis_client.setex(
                idempotency_key_redis,
                self.idempotency_ttl,
                "1"
            )
            logger.info(f"Idempotency key set: {idempotency_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to set idempotency key: {e}")
            return False
    
    def ping(self) -> bool:
        """Test Redis connection"""
        try:
            return self.redis_client.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False


# Singleton instance
redis_client = RedisClient()


"""
Base Verification Handler
Preserves interface from app/verification/base.py
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class BaseVerifier(ABC):
    """Abstract base class for payment verification"""
    
    @abstractmethod
    def verify(self, transaction_uuid: str, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify payment transaction.
        
        Args:
            transaction_uuid: Transaction UUID
            callback_data: Callback data from gateway
            
        Returns:
            Dict containing verification result
        """
        raise NotImplementedError


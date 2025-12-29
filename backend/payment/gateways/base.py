"""
Base Gateway Abstract Class
Preserves existing gateway interface from app/gateways
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class BaseGateway(ABC):
    """
    Abstract base class for payment gateways.
    Preserves the interface from app/gateways/base.py
    """
    
    def __init__(self, transaction_handler=None, **config: Dict[str, Any]):
        """
        Initialize payment gateway.
        
        Args:
            transaction_handler: Transaction handler instance (optional in Django)
            **config: Gateway configuration
        """
        self.transaction_handler = transaction_handler
        self.config = config
        logger.info(f"Initializing {self.__class__.__name__}")
    
    @abstractmethod
    def create_payment(self, amount: int, currency: str, **kwargs) -> Dict[str, Any]:
        """
        Create payment request.
        
        Args:
            amount: Payment amount
            currency: Currency code
            **kwargs: Additional parameters
            
        Returns:
            Dict containing payment request response
        """
        raise NotImplementedError
    
    @abstractmethod
    def verify_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify payment transaction.
        
        Args:
            data: Verification data from gateway callback
            
        Returns:
            Dict containing verification response
        """
        raise NotImplementedError
    
    def get_default_callback_url(self) -> str:
        """Get default callback URL from settings"""
        gateway_name = self.__class__.__name__.lower().replace('gateway', '')
        return settings.PAYMENT_SETTINGS.get(
            gateway_name.upper(),
            {}
        ).get('CALLBACK_URL', '')


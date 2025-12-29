"""
Zarinpal Gateway Implementation
Preserves logic from app/gateways/zarinpal.py
"""
import requests
import json
import logging
from typing import Dict, Any, Optional
from django.conf import settings
from .base import BaseGateway

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30


class ZarinpalGateway(BaseGateway):
    """Zarinpal payment gateway implementation"""
    
    def __init__(self, **config):
        super().__init__(**config)
        self.merchant_id = config.get('merchant_id') or settings.PAYMENT_SETTINGS['ZARINPAL']['MERCHANT_ID']
        self.api_request_url = config.get('api_request_url') or settings.PAYMENT_SETTINGS['ZARINPAL']['API_REQUEST_URL']
        self.api_verify_url = config.get('api_verify_url') or settings.PAYMENT_SETTINGS['ZARINPAL']['API_VERIFY_URL']
    
    def create_payment(self, amount: int, currency: str, **kwargs) -> Dict[str, Any]:
        """
        Create payment request with Zarinpal.
        Preserves logic from app/gateways/zarinpal.py send_request_zarinpall
        """
        callback_url = kwargs.get('callback_url') or self.get_default_callback_url()
        description = kwargs.get('description', '')
        email = kwargs.get('email')
        mobile = kwargs.get('mobile')
        metadata = kwargs.get('metadata', {})
        
        if email or mobile:
            metadata.update({
                'mobile': mobile,
                'email': email
            })
        
        req_data = {
            "merchant_id": str(self.merchant_id),
            "amount": str(amount),
            "callback_url": str(callback_url),
            "description": str(description),
            "metadata": metadata if metadata else {}
        }
        
        req_headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }
        
        logger.info(f"Sending payment request to Zarinpal: amount={amount}, merchant={self.merchant_id}")
        
        try:
            response = requests.post(
                url=self.api_request_url,
                data=json.dumps(req_data),
                headers=req_headers,
                timeout=DEFAULT_TIMEOUT
            )
            response.raise_for_status()
            response_data = response.json()
            
            # Check for errors
            if 'errors' in response_data and len(response_data['errors']) > 0:
                error_info = response_data['errors'][0]
                return {
                    "status": "error",
                    "message": error_info.get('message', 'Unknown error'),
                    "error_code": error_info.get('code', 'unknown'),
                    "errors": response_data['errors']
                }
            
            # Success response
            if 'data' in response_data:
                return {
                    "status": "success",
                    "data": response_data['data'],
                    "errors": []
                }
            
            return {
                "status": "error",
                "message": "Unexpected response format",
                "error_code": "UNEXPECTED_FORMAT"
            }
            
        except requests.Timeout:
            logger.error(f"Request timeout after {DEFAULT_TIMEOUT}s")
            return {
                "status": "error",
                "message": "Request timeout",
                "error_code": "TIMEOUT"
            }
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "error_code": "REQUEST_ERROR"
            }
    
    def verify_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify payment with Zarinpal.
        Preserves logic from app/verification/zarinpal_verifier.py
        """
        authority = data.get('authority') or data.get('authority_code')
        amount = data.get('amount')
        
        if not authority or not amount:
            return {
                "status": "error",
                "transaction": False,
                "pay": False,
                "message": "Missing authority or amount",
                "error_code": "MISSING_PARAMS"
            }
        
        req_data = {
            "merchant_id": str(self.merchant_id),
            "amount": str(amount),
            "authority": str(authority)
        }
        
        req_headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }
        
        logger.info(f"Verifying payment with Zarinpal: authority={authority}, amount={amount}")
        
        try:
            response = requests.post(
                url=self.api_verify_url,
                data=json.dumps(req_data),
                headers=req_headers,
                timeout=DEFAULT_TIMEOUT
            )
            response.raise_for_status()
            response_data = response.json()
            
            # Check for errors
            if 'errors' in response_data and len(response_data['errors']) > 0:
                error_info = response_data['errors'][0]
                return {
                    "status": "error",
                    "transaction": False,
                    "pay": False,
                    "message": error_info.get('message', 'Unknown error'),
                    "error_code": error_info.get('code', 'unknown'),
                    "RefID": None
                }
            
            # Process verification response
            if 'data' in response_data:
                verify_status_code = response_data['data'].get('code')
                verify_message = response_data['data'].get('message', '')
                
                # Status code 100: Payment successful
                if verify_status_code == 100:
                    ref_id = response_data['data'].get('ref_id')
                    return {
                        "status": "success",
                        "transaction": True,
                        "pay": True,
                        "RefID": ref_id,
                        "message": verify_message or "Payment verified successfully"
                    }
                
                # Status code 101: Payment already verified
                elif verify_status_code == 101:
                    return {
                        "status": "already_verified",
                        "transaction": True,
                        "pay": False,
                        "RefID": None,
                        "message": verify_message or "Payment already verified"
                    }
                
                # Other status codes: Payment failed
                else:
                    return {
                        "status": "failed",
                        "transaction": False,
                        "pay": False,
                        "RefID": None,
                        "message": verify_message or "Payment verification failed"
                    }
            
            return {
                "status": "error",
                "transaction": False,
                "pay": False,
                "message": "Unexpected response format",
                "error_code": "UNEXPECTED_FORMAT",
                "RefID": None
            }
            
        except requests.Timeout:
            return {
                "status": "error",
                "transaction": False,
                "pay": False,
                "message": "Request timeout",
                "error_code": "TIMEOUT",
                "RefID": None
            }
        except requests.RequestException as e:
            logger.error(f"Verification request failed: {e}")
            return {
                "status": "error",
                "transaction": False,
                "pay": False,
                "message": str(e),
                "error_code": "REQUEST_ERROR",
                "RefID": None
            }


from django.db import models


class TransactionStatus(models.TextChoices):
    """Transaction status enumeration"""
    PENDING = 'pending', 'Pending'
    COMPLETED = 'completed', 'Completed'
    COMPLETED_AND_ADDED = 'completed_and_added', 'Completed and Added to Wallet'
    FAILED = 'failed', 'Failed'
    REFUNDED = 'refunded', 'Refunded'
    CANCELLED = 'cancelled', 'Cancelled'


class GatewayType(models.IntegerChoices):
    """Payment gateway type enumeration"""
    ZARINPAL = 1, 'Zarinpal'
    STRIPE = 2, 'Stripe'
    PAYPAL = 3, 'PayPal'


"""
Django ORM Models for Payment Transactions
"""
import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from .enums import TransactionStatus, GatewayType


class Transaction(models.Model):
    """
    Payment Transaction Model
    
    Represents a payment transaction with all necessary fields
    for tracking payment state and preventing double spending.
    """
    transaction_uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_index=True,
        help_text="Unique transaction identifier"
    )
    
    order_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Order identifier from merchant system"
    )
    
    user_id = models.UUIDField(
        db_index=True,
        help_text="User identifier"
    )
    
    gateway_id = models.IntegerField(
        choices=GatewayType.choices,
        db_index=True,
        help_text="Payment gateway identifier"
    )
    
    amount = models.BigIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Transaction amount in smallest currency unit"
    )
    
    currency = models.CharField(
        max_length=10,
        default='IRR',
        help_text="Currency code (ISO 4217)"
    )
    
    description = models.TextField(
        help_text="Transaction description"
    )
    
    authority_code = models.CharField(
        max_length=255,
        db_index=True,
        null=True,
        blank=True,
        help_text="Payment gateway authority/reference code"
    )
    
    ref_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="Reference ID from payment gateway after verification"
    )
    
    meta = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata (JSON)"
    )
    
    idempotency_key = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Idempotency key for preventing duplicate requests"
    )
    
    # Status flags
    is_done = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether transaction is completed"
    )
    
    is_added_wallet = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether amount has been added to wallet"
    )
    
    is_refund = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether transaction is refunded"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    
    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    class Meta:
        db_table = 'transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_id', 'user_id']),
            models.Index(fields=['gateway_id', 'is_done']),
            models.Index(fields=['created_at', 'is_done']),
        ]
    
    def __str__(self):
        return f"Transaction {self.transaction_uuid} - {self.order_id}"
    
    @property
    def status(self) -> str:
        """Get transaction status string"""
        if self.is_refund:
            return TransactionStatus.REFUNDED
        elif self.is_done:
            if self.is_added_wallet:
                return TransactionStatus.COMPLETED_AND_ADDED
            return TransactionStatus.COMPLETED
        return TransactionStatus.PENDING
    
    def mark_as_completed(self, ref_id: str = None):
        """Mark transaction as completed"""
        self.is_done = True
        if ref_id:
            self.ref_id = ref_id
        self.save(update_fields=['is_done', 'ref_id', 'updated_at'])
    
    def mark_as_refunded(self):
        """Mark transaction as refunded"""
        self.is_refund = True
        self.save(update_fields=['is_refund', 'updated_at'])


class TransactionEvent(models.Model):
    """
    Transaction Event Log Model
    
    Tracks all state changes and events for a transaction
    for audit and debugging purposes.
    """
    id = models.BigAutoField(primary_key=True)
    
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name='events',
        db_index=True
    )
    
    old_status = models.CharField(
        max_length=50,
        help_text="Previous transaction status"
    )
    
    new_status = models.CharField(
        max_length=50,
        help_text="New transaction status"
    )
    
    event_source = models.CharField(
        max_length=100,
        help_text="Source of the event (e.g., 'payment_gateway', 'webhook')"
    )
    
    payload = models.JSONField(
        default=dict,
        help_text="Event payload data (JSON)"
    )
    
    provider_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the event provider"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    
    class Meta:
        db_table = 'transaction_event'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction', 'created_at']),
        ]
    
    def __str__(self):
        return f"Event {self.id} - {self.old_status} -> {self.new_status}"


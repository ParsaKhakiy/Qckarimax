"""
DRF Serializers for Payment API
"""
from rest_framework import serializers
from payment.models import Transaction, GatewayType


class PaymentInitializeSerializer(serializers.Serializer):
    """Serializer for payment initialization request"""
    amount = serializers.IntegerField(min_value=1, help_text="Transaction amount")
    currency = serializers.CharField(max_length=10, default='IRR', help_text="Currency code")
    gateway = serializers.ChoiceField(
        choices=[(gt.value, gt.label) for gt in GatewayType],
        help_text="Payment gateway type"
    )
    order_id = serializers.CharField(max_length=255, help_text="Order identifier")
    user_id = serializers.UUIDField(help_text="User identifier")
    description = serializers.CharField(required=False, allow_blank=True, help_text="Transaction description")
    callback_url = serializers.URLField(required=False, help_text="Custom callback URL")
    idempotency_key = serializers.CharField(max_length=255, required=False, help_text="Idempotency key")
    metadata = serializers.JSONField(required=False, default=dict, help_text="Additional metadata")
    
    def validate_gateway(self, value):
        """Validate gateway value"""
        try:
            GatewayType(value)
        except ValueError:
            raise serializers.ValidationError(f"Invalid gateway: {value}")
        return value


class PaymentInitializeResponseSerializer(serializers.Serializer):
    """Serializer for payment initialization response"""
    payment_id = serializers.UUIDField(help_text="Payment transaction UUID")
    redirect_url = serializers.URLField(help_text="Payment gateway redirect URL")
    authority_code = serializers.CharField(help_text="Gateway authority code")


class PaymentVerifySerializer(serializers.Serializer):
    """Serializer for payment verification request"""
    payment_id = serializers.UUIDField(help_text="Payment transaction UUID")
    callback_data = serializers.JSONField(help_text="Callback data from gateway")
    idempotency_key = serializers.CharField(max_length=255, required=False, help_text="Idempotency key for verification")


class PaymentVerifyResponseSerializer(serializers.Serializer):
    """Serializer for payment verification response"""
    status = serializers.CharField(help_text="Verification status")
    payment_id = serializers.UUIDField(help_text="Payment transaction UUID")
    tracking_code = serializers.CharField(required=False, allow_null=True, help_text="Tracking/reference code")
    ref_id = serializers.CharField(required=False, allow_null=True, help_text="Reference ID from gateway")
    message = serializers.CharField(help_text="Status message")


class PaymentStatusSerializer(serializers.ModelSerializer):
    """Serializer for payment status response"""
    status = serializers.CharField(read_only=True)
    payment_id = serializers.UUIDField(source='transaction_uuid', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'payment_id',
            'status',
            'amount',
            'currency',
            'gateway_id',
            'order_id',
            'is_done',
            'is_added_wallet',
            'is_refund',
            'ref_id',
            'created_at',
        ]
        read_only_fields = fields


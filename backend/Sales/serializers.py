from django.utils.module_loading import import_string
from django.conf import settings 


# TokenObtainClass = import_string(
#     settings.TOKEN_OBTAIN_SERIALIZER0
# )


from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import SalesExpert, OrderHistoryCreator
from order.models import Order

User = get_user_model()

class UserSimpleSerializer(serializers.ModelSerializer):
    """سریالایزر ساده برای نمایش اطلاعات کاربر"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id']


class SalesExpertSerializer(serializers.ModelSerializer):
    """سریالایزر برای کارشناس فروش"""
    user = UserSimpleSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        source='user',
        required=True
    )
    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SalesExpert
        fields = [
            'id',
            'user',
            'user_id',
            'full_name',
            'employee_code',
            'branch',
            'total_sales_amount'
        ]
        read_only_fields = ['id', 'full_name', 'total_sales_amount']

    def get_full_name(self, obj):
        """دریافت نام کامل کاربر"""
        return obj.user.get_full_name() if obj.user else ''

    def validate_employee_code(self, value):
        """اعتبارسنجی کد پرسنلی"""
        # بررسی تکراری نبودن کد پرسنلی
        if SalesExpert.objects.filter(employee_code=value).exists():
            if self.instance and self.instance.employee_code == value:
                return value
            raise serializers.ValidationError("کد پرسنلی تکراری است.")
        return value

    def create(self, validated_data):
        """ایجاد کارشناس فروش"""
        return SalesExpert.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """بروزرسانی کارشناس فروش"""
        # به روزرسانی فیلدها
        instance.employee_code = validated_data.get('employee_code', instance.employee_code)
        instance.branch = validated_data.get('branch', instance.branch)
        
        # به روزرسانی کاربر در صورت نیاز
        if 'user' in validated_data:
            instance.user = validated_data['user']
        
        instance.save()
        return instance


class SalesExpertListSerializer(serializers.ModelSerializer):
    """سریالایزر مختصر برای لیست کارشناسان فروش"""
    full_name = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = SalesExpert
        fields = [
            'id',
            'employee_code',
            'full_name',
            'user_email',
            'branch',
            'total_sales_amount'
        ]
        read_only_fields = fields

    def get_full_name(self, obj):
        return obj.user.get_full_name() if obj.user else ''

    def get_user_email(self, obj):
        return obj.user.email if obj.user else ''


class OrderSimpleSerializer(serializers.ModelSerializer):
    """سریالایزر ساده برای سفارش"""
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'order_date', 'total_amount', 'status']
        read_only_fields = fields


class OrderHistoryCreatorSerializer(serializers.ModelSerializer):
    """سریالایزر برای تاریخچه سفارشات"""
    saleser = SalesExpertListSerializer(read_only=True)
    saleser_id = serializers.PrimaryKeyRelatedField(
        queryset=SalesExpert.objects.all(),
        write_only=True,
        source='saleser',
        required=True
    )
    orders = OrderSimpleSerializer(many=True, read_only=True)
    order_ids = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(),
        many=True,
        write_only=True,
        source='orders',
        required=False
    )

    class Meta:
        model = OrderHistoryCreator
        fields = [
            'id',
            'saleser',
            'saleser_id',
            'orders',
            'order_ids',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        """ایجاد تاریخچه سفارشات"""
        orders = validated_data.pop('orders', [])
        order_history = OrderHistoryCreator.objects.create(**validated_data)
        
        if orders:
            order_history.orders.set(orders)
        
        return order_history

    def update(self, instance, validated_data):
        """بروزرسانی تاریخچه سفارشات"""
        orders = validated_data.pop('orders', None)
        
        # به روزرسانی saleser در صورت نیاز
        if 'saleser' in validated_data:
            instance.saleser = validated_data['saleser']
        
        instance.save()
        
        # به روزرسانی سفارشات در صورت نیاز
        if orders is not None:
            instance.orders.set(orders)
        
        return instance


class OrderHistoryCreatorDetailSerializer(serializers.ModelSerializer):
    """سریالایزر جزئیات برای تاریخچه سفارشات"""
    saleser = SalesExpertSerializer(read_only=True)
    orders = OrderSimpleSerializer(many=True, read_only=True)

    class Meta:
        model = OrderHistoryCreator
        fields = [
            'id',
            'saleser',
            'orders',
            'created_at',
            'updated_at'
        ]
        read_only_fields = fields


class SalesExpertStatisticsSerializer(serializers.ModelSerializer):
    """سریالایزر برای آمار کارشناس فروش"""
    full_name = serializers.SerializerMethodField()
    order_count = serializers.SerializerMethodField()
    average_order_amount = serializers.SerializerMethodField()

    class Meta:
        model = SalesExpert
        fields = [
            'id',
            'employee_code',
            'full_name',
            'branch',
            'total_sales_amount',
            'order_count',
            'average_order_amount',
            'mount_sale_amount',
            'product_added',
            'customer_satisfaction',
            'total_sales_product_amount',

        ]
        read_only_fields = fields

    def get_full_name(self, obj):
        return obj.user.get_full_name() if obj.user else ''

    def get_order_count(self, obj):
        try:
            order_history = obj.OrderHistory
            return order_history.orders.count()
        
        except OrderHistoryCreator.DoesNotExist:
            return 0

    def get_average_order_amount(self, obj):
        """میانگین مبلغ سفارشات"""
        try:
            order_history = obj.OrderHistory
            order_count = order_history.orders.count() # TODO MUST BE CACHE FOR each user 
            if order_count > 0 and obj.total_sales_amount:
                return obj.total_sales_amount / order_count
            return 0
        except (OrderHistoryCreator.DoesNotExist, ZeroDivisionError):
            return 0


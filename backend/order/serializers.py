from rest_framework import serializers
from django.utils import timezone
from .models import Order
from product.models import Product
from Sales.models import SalesExpert


class OrderInputSerializer(serializers.ModelSerializer):
    # تغییر از ForeignKey به PrimaryKeyRelatedField برای ارسال ID
    saler_id = serializers.PrimaryKeyRelatedField(
        queryset=SalesExpert.objects.all(),
        source='saler',
        write_only=True,
        required=False  # اختیاری چون در view خودکار پر می‌شود
    )
    
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True),
        source='product',
        write_only=True
    )

    class Meta:
        model = Order
        # فقط فیلدهایی که کاربر باید ارسال کند
        fields = [
            'saler_id', 'name', 'description', 'customer_name', 
            'customer_family', 'address', 'postal_code', 
            'city', 'product_id', 'total_price'
        ]
        # حذف فیلدهایی که نباید از کاربر بگیریم
        extra_kwargs = {
            'saler_id': {'required': False},  # در view پر می‌شود
            'name': {'required': False}  # اگر خالی باشد، خودکار ایجاد می‌شود
        }

    def validate_postal_code(self, value):
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError("کد پستی باید ۱۰ رقم عدد باشد.")
        return value

    def validate_total_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("قیمت کل باید بیشتر از صفر باشد.")
        return value

    def create(self, validated_data):
        # اضافه کردن نام پیش‌فرض اگر خالی باشد
        if not validated_data.get('name'):
            validated_data['name'] = f"سفارش {timezone.now().strftime('%Y%m%d-%H%M%S')}"
        
        return super().create(validated_data)


class OrderOutputSerializer(serializers.ModelSerializer):
    # نمایش نام کارشناس و محصول به جای ID
    saler_name = serializers.CharField(source='saler.user.get_full_name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    full_customer_name = serializers.SerializerMethodField()
    
    # اضافه کردن IDها برای خوانایی
    saler_id = serializers.IntegerField(source='saler.id', read_only=True)
    product_id = serializers.IntegerField(source='product.id', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'saler', 'saler_id', 'saler_name', 'name', 'description', 
            'customer_name', 'customer_family', 'full_customer_name',
            'address', 'postal_code', 'city', 
            'product', 'product_id', 'product_name',
            'status', 'status_display', 'total_price', 'tracking_code', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'tracking_code', 'status']

    def get_full_customer_name(self, obj):
        return f"{obj.customer_name} {obj.customer_family}"
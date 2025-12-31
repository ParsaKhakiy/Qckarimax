from rest_framework import serializers
from .models import Order

class OrderOutputSerializer(serializers.ModelSerializer):
    # نمایش نام کارشناس و محصول به جای ID
    saler_name = serializers.CharField(source='saler.user.get_full_name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'saler', 'saler_name', 'name', 'description', 
            'customer_name', 'customer_family', 'full_customer_name',
            'address', 'postal_code', 'city', 'product', 'product_name',
            'status', 'status_display', 'total_price', 'tracking_code', 
            'created_at'
        ]

class OrderInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        # فیلدهایی که کاربر باید بفرستد
        fields = [
            'saler', 'name', 'description', 'customer_name', 
            'customer_family', 'address', 'postal_code', 
            'city', 'product', 'total_price'
        ]

    def validate_postal_code(self, value):
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError("کد پستی باید ۱۰ رقم عدد باشد.")
        return value

    def validate_total_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("قیمت کل باید بیشتر از صفر باشد.")
        return value

# serializers/category.py
from rest_framework import serializers
from django.utils.text import slugify

from .models import (
    Category,
    Product,
    Requirements,
    Operator,
    ProductionLine,
    ProductionTask,
    RequirementsProducts , 

)

from order.models import Order


class CategoryInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['title', 'slug']
        extra_kwargs = {
            'slug': {'required': False}
        }

    def create(self, validated_data):
        if 'slug' not in validated_data or not validated_data['slug']:
            validated_data['slug'] = slugify(validated_data['title'], allow_unicode=True)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'title' in validated_data and ('slug' not in validated_data or not validated_data['slug']):
            validated_data['slug'] = slugify(validated_data['title'], allow_unicode=True)
        return super().update(instance, validated_data)


class CategoryOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'slug']
        read_only_fields = ['id']




# serializers/product.py
class ProductInputSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Product
        fields = [
            'name', 'description', 'slug', 'is_active',
            'category_id', 'price', 'discount_price', 'stock'
        ]
        extra_kwargs = {
            'slug': {'required': False}
        }

    def create(self, validated_data):
        if 'slug' not in validated_data or not validated_data['slug']:
            validated_data['slug'] = slugify(validated_data['name'], allow_unicode=True)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'name' in validated_data and ('slug' not in validated_data or not validated_data['slug']):
            validated_data['slug'] = slugify(validated_data['name'], allow_unicode=True)
        return super().update(instance, validated_data)


class ProductOutputSerializer(serializers.ModelSerializer):
    category = CategoryOutputSerializer(read_only=True)
    category_id = serializers.IntegerField(source='category.id', read_only=True)
    category_name = serializers.CharField(source='category.title', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'slug', 'is_active',
            'category', 'category_id', 'category_name',
            'price', 'discount_price', 'final_price', 'stock',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'final_price', 'created_at', 'updated_at']




# serializers/requirements.py
class RequirementsInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Requirements
        fields = ['name', 'description', 'slug', 'is_active']
        extra_kwargs = {
            'slug': {'required': False}
        }

    def create(self, validated_data):
        if 'slug' not in validated_data or not validated_data['slug']:
            validated_data['slug'] = slugify(validated_data['name'], allow_unicode=True)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'name' in validated_data and ('slug' not in validated_data or not validated_data['slug']):
            validated_data['slug'] = slugify(validated_data['name'], allow_unicode=True)
        return super().update(instance, validated_data)


class RequirementsOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Requirements
        fields = ['id', 'name', 'description', 'slug', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


# serializers/operator.py

class OperatorInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operator
        fields = ['name', 'family', 'description', 'slug', 'is_active']
        extra_kwargs = {
            'slug': {'required': False}
        }

    def create(self, validated_data):
        if 'slug' not in validated_data or not validated_data['slug']:
            full_name = f"{validated_data['name']} {validated_data['family']}"
            validated_data['slug'] = slugify(full_name, allow_unicode=True)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if ('name' in validated_data or 'family' in validated_data) and ('slug' not in validated_data or not validated_data['slug']):
            name = validated_data.get('name', instance.name)
            family = validated_data.get('family', instance.family)
            full_name = f"{name} {family}"
            validated_data['slug'] = slugify(full_name, allow_unicode=True)
        return super().update(instance, validated_data)


class OperatorOutputSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Operator
        fields = ['id', 'name', 'family', 'full_name', 'description', 'slug', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'full_name', 'created_at', 'updated_at']

    def get_full_name(self, obj):
        return f"{obj.name} {obj.family}"
    

# serializers/production_line.py
class ProductionLineInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionLine
        fields = ['name', 'location', 'capacity', 'is_active']


class ProductionLineOutputSerializer(serializers.ModelSerializer):
    active_tasks_count = serializers.IntegerField(read_only=True)
    has_free_capacity = serializers.BooleanField(read_only=True)

    class Meta:
        model = ProductionLine
        fields = ['id', 'name', 'location', 'capacity', 'is_active', 
                 'active_tasks_count', 'has_free_capacity']
        read_only_fields = ['id', 'active_tasks_count', 'has_free_capacity']


# serializers/production_task.py
class ProductionTaskInputSerializer(serializers.ModelSerializer):
    order_id = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(),
        source='order',
        write_only=True
    )
    production_line_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductionLine.objects.filter(is_active=True),
        source='production_line',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = ProductionTask
        fields = ['order_id', 'production_line_id', 'status', 
                 'timeline', 'start_date', 'end_date']


class ProductionTaskOutputSerializer(serializers.ModelSerializer):
    order = serializers.PrimaryKeyRelatedField(read_only=True)
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    
    production_line = ProductionLineOutputSerializer(read_only=True)
    production_line_id = serializers.IntegerField(source='production_line.id', read_only=True)
    production_line_name = serializers.CharField(source='production_line.name', read_only=True)
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ProductionTask
        fields = [
            'id', 'order', 'order_id', 
            'production_line', 'production_line_id', 'production_line_name',
            'status', 'status_display', 'timeline',
            'start_date', 'end_date'
        ]
        read_only_fields = ['id', 'status_display']




# serializers/requirements_products.py
class RequirementsProductsInputSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    requirements_ids = serializers.PrimaryKeyRelatedField(
        queryset=Requirements.objects.all(),
        source='requirements',
        write_only=True,
        many=True
    )
    product_timeline_ids = serializers.PrimaryKeyRelatedField(
        queryset=ProductionLine.objects.all(),
        source='product_timeline',
        write_only=True,
        many=True
    )
    operator_ids = serializers.PrimaryKeyRelatedField(
        queryset=Operator.objects.all(),
        source='operators',
        write_only=True,
        many=True
    )

    class Meta:
        model = RequirementsProducts
        fields = ['name', 'description', 'slug', 'is_active',
                 'product_id', 'requirements_ids', 'product_timeline_ids', 'operator_ids']
        extra_kwargs = {
            'slug': {'required': False}
        }

    def create(self, validated_data):
        if 'slug' not in validated_data or not validated_data['slug']:
            validated_data['slug'] = slugify(validated_data['name'], allow_unicode=True)
        return super().create(validated_data)


class RequirementsProductsOutputSerializer(serializers.ModelSerializer):
    product = ProductOutputSerializer(read_only=True)
    product_id = serializers.IntegerField(source='product.id', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    requirements = RequirementsOutputSerializer(many=True, read_only=True)
    requirements_ids = serializers.SerializerMethodField(read_only=True)
    
    product_timeline = ProductionLineOutputSerializer(many=True, read_only=True)
    product_timeline_ids = serializers.SerializerMethodField(read_only=True)
    
    operators = OperatorOutputSerializer(many=True, read_only=True)
    operator_ids = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = RequirementsProducts
        fields = [
            'id', 'name', 'description', 'slug', 'is_active',
            'product', 'product_id', 'product_name',
            'requirements', 'requirements_ids',
            'product_timeline', 'product_timeline_ids',
            'operators', 'operator_ids',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_requirements_ids(self, obj):
        return list(obj.requirements.values_list('id', flat=True))

    def get_product_timeline_ids(self, obj):
        return list(obj.product_timeline.values_list('id', flat=True))

    def get_operator_ids(self, obj):
        return list(obj.operators.values_list('id', flat=True))
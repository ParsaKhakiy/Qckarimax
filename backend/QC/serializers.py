# serializers/production_card.py
from rest_framework import serializers
from django.utils import timezone
from .models import ProductionCard, QualityControlExpert

from product.models import RequirementsProducts

from django.utils.text import slugify
import random
import string




class ProductionCardInputSerializer(serializers.ModelSerializer):
    requirements_product_id = serializers.PrimaryKeyRelatedField(
        queryset=RequirementsProducts.objects.filter(is_active=True),
        source='requirements_product',
        write_only=True,
        required=True
    )
    
    created_by_id = serializers.PrimaryKeyRelatedField(
        queryset=QualityControlExpert.objects.all(),
        source='created_by',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    approved_by_qa_id = serializers.PrimaryKeyRelatedField(
        queryset=QualityControlExpert.objects.all(),
        source='approved_by_qa',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = ProductionCard
        fields = [
            'title',
            'requirements_product_id',
            'status',
            'priority',
            'quantity_to_produce',
            'estimated_duration',
            'scheduled_start_date',
            'scheduled_end_date',
            'actual_start_date',
            'actual_end_date',
            'current_progress',
            'required_materials',
            'required_components',
            'required_tools',
            'production_standards',
            'special_instructions',
            'qc_required',
            'qc_checkpoints',
            'approved_by_qa_id',
            'approval_date',
            'attachments',
            'notes',
            'is_active',
            'created_by_id',
        ]
        read_only_fields = ['card_code']
    
    def validate(self, data):
        # اعتبارسنجی تاریخ‌ها
        scheduled_start = data.get('scheduled_start_date')
        scheduled_end = data.get('scheduled_end_date')
        actual_start = data.get('actual_start_date')
        actual_end = data.get('actual_end_date')
        
        if scheduled_start and scheduled_end and scheduled_start >= scheduled_end:
            raise serializers.ValidationError({
                'scheduled_end_date': 'تاریخ پایان باید بعد از تاریخ شروع باشد'
            })
        
        if actual_start and actual_end and actual_start >= actual_end:
            raise serializers.ValidationError({
                'actual_end_date': 'تاریخ پایان واقعی باید بعد از تاریخ شروع واقعی باشد'
            })
        
        # اعتبارسنجی پیشرفت
        current_progress = data.get('current_progress', 0)
        if current_progress < 0 or current_progress > 100:
            raise serializers.ValidationError({
                'current_progress': 'درصد پیشرفت باید بین ۰ تا ۱۰۰ باشد'
            })
        
        # اعتبارسنجی تعداد
        quantity = data.get('quantity_to_produce', 1)
        if quantity < 1:
            raise serializers.ValidationError({
                'quantity_to_produce': 'تعداد باید حداقل ۱ باشد'
            })
        
        # اعتبارسنجی نقاط کنترل کیفیت
        qc_checkpoints = data.get('qc_checkpoints', 1)
        if qc_checkpoints < 1:
            raise serializers.ValidationError({
                'qc_checkpoints': 'تعداد نقاط کنترل کیفیت باید حداقل ۱ باشد'
            })
        
        return data
    
    def create(self, validated_data):
        # تولید کد کارت تولید
        prefix = "PC"
        year_month = timezone.now().strftime("%y%m")
        random_suffix = ''.join(random.choices(string.digits, k=4))
        validated_data['card_code'] = f"{prefix}{year_month}{random_suffix}"
        
        # تنظیم کاربر ایجاد کننده اگر ارسال نشده
        request = self.context.get('request')
        if request and request.user and 'created_by' not in validated_data:
            try:
                qc_expert = QualityControlExpert.objects.get(user=request.user)
                validated_data['created_by'] = qc_expert
            except QualityControlExpert.DoesNotExist:
                pass
        
        # تنظیم وضعیت اولیه
        if 'status' not in validated_data:
            validated_data['status'] = 'draft'
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # مدیریت تغییر وضعیت
        if 'status' in validated_data:
            old_status = instance.status
            new_status = validated_data['status']
            
            # تاریخ‌های شروع و پایان را بر اساس وضعیت تنظیم کن
            if new_status == 'in_production' and not instance.actual_start_date:
                validated_data['actual_start_date'] = timezone.now()
            elif new_status in ['completed', 'archived'] and not instance.actual_end_date:
                validated_data['actual_end_date'] = timezone.now()
            elif new_status == 'approved' and not instance.approval_date:
                validated_data['approval_date'] = timezone.now()
        
        return super().update(instance, validated_data)
    





class ProductionCardOutputSerializer(serializers.ModelSerializer):
    requirements_product = serializers.SerializerMethodField()
    requirements_product_id = serializers.IntegerField(source='requirements_product.id', read_only=True)
    requirements_product_name = serializers.CharField(source='requirements_product.name', read_only=True)
    
    created_by = serializers.SerializerMethodField()
    created_by_id = serializers.IntegerField(source='created_by.id', read_only=True)
    created_by_fullname = serializers.SerializerMethodField()
    
    approved_by_qa = serializers.SerializerMethodField()
    approved_by_qa_id = serializers.IntegerField(source='approved_by_qa.id', read_only=True)
    approved_by_qa_fullname = serializers.SerializerMethodField()
    
    product_info = serializers.SerializerMethodField()
    estimated_duration_hours = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    is_overdue = serializers.SerializerMethodField()
    remaining_days = serializers.SerializerMethodField()
    production_efficiency = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductionCard
        fields = [
            'id',
            'card_code',
            'title',
            
            # اطلاعات محصول و الزامات
            'requirements_product',
            'requirements_product_id',
            'requirements_product_name',
            'product_info',
            
            # وضعیت و اولویت
            'status',
            'status_display',
            'priority',
            'priority_display',
            'quantity_to_produce',
            
            # زمان‌بندی
            'estimated_duration',
            'estimated_duration_hours',
            'scheduled_start_date',
            'scheduled_end_date',
            'actual_start_date',
            'actual_end_date',
            
            # پیشرفت
            'current_progress',
            
            # مواد و قطعات
            'required_materials',
            'required_components',
            'required_tools',
            
            # استانداردها
            'production_standards',
            'special_instructions',
            
            # کنترل کیفیت
            'qc_required',
            'qc_checkpoints',
            'approved_by_qa',
            'approved_by_qa_id',
            'approved_by_qa_fullname',
            'approval_date',
            
            # پیوست‌ها
            'attachments',
            
            # متا اطلاعات
            'notes',
            'is_active',
            'created_by',
            'created_by_id',
            'created_by_fullname',
            'created_at',
            'updated_at',
            
            # فیلدهای محاسباتی
            'is_overdue',
            'remaining_days',
            'production_efficiency',
        ]
        read_only_fields = ['id', 'card_code', 'created_at', 'updated_at']
    
    def get_requirements_product(self, obj):
        from product.serializers import RequirementsProductsOutputSerializer
        return RequirementsProductsOutputSerializer(obj.requirements_product).data
    
    def get_created_by(self, obj):
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'username': obj.created_by.user.username if obj.created_by.user else None,
            }
        return None
    
    def get_created_by_fullname(self, obj):
        if obj.created_by and hasattr(obj.created_by, 'user'):
            user = obj.created_by.user
            return f"{user.first_name} {user.last_name}".strip() or user.username
        return None
    
    def get_approved_by_qa(self, obj):
        if obj.approved_by_qa:
            return {
                'id': obj.approved_by_qa.id,
                'username': obj.approved_by_qa.user.username if obj.approved_by_qa.user else None,
            }
        return None
    
    def get_approved_by_qa_fullname(self, obj):
        if obj.approved_by_qa and hasattr(obj.approved_by_qa, 'user'):
            user = obj.approved_by_qa.user
            return f"{user.first_name} {user.last_name}".strip() or user.username
        return None
    
    def get_product_info(self, obj):
        """نمایش اطلاعات محصول مرتبط"""
        if obj.requirements_product and obj.requirements_product.product:
            product = obj.requirements_product.product
            return {
                'product_id': product.id,
                'product_name': product.name,
                'product_description': product.description,
                'category': product.category.title if product.category else None,
            }
        return None
    
    def get_estimated_duration_hours(self, obj):
        """تبدیل duration به ساعت"""
        if obj.estimated_duration:
            total_seconds = obj.estimated_duration.total_seconds()
            return round(total_seconds / 3600, 2)  # تبدیل به ساعت
        return None
    
    def get_is_overdue(self, obj):
        """بررسی تأخیر در تولید"""
        if obj.status not in ['completed', 'archived'] and obj.scheduled_end_date:
            return timezone.now() > obj.scheduled_end_date
        return False
    
    def get_remaining_days(self, obj):
        """محاسبه روزهای باقی‌مانده"""
        if obj.status not in ['completed', 'archived'] and obj.scheduled_end_date:
            remaining = obj.scheduled_end_date - timezone.now()
            return max(0, remaining.days)
        return 0
    
    def get_production_efficiency(self, obj):
        """محاسبه کارایی تولید"""
        if obj.actual_start_date and obj.current_progress > 0:
            if obj.estimated_duration:
                estimated_hours = obj.estimated_duration.total_seconds() / 3600
                progress_percentage = obj.current_progress / 100
                
                if obj.actual_start_date:
                    elapsed_time = (timezone.now() - obj.actual_start_date).total_seconds() / 3600
                    if elapsed_time > 0:
                        efficiency = (progress_percentage * estimated_hours) / elapsed_time
                        return round(efficiency * 100, 2)  # درصد کارایی
        return None
    


class ProductionCardLiteSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    product_name = serializers.CharField(source='requirements_product.product.name', read_only=True)
    is_overdue = serializers.SerializerMethodField()
    remaining_days = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductionCard
        fields = [
            'id',
            'card_code',
            'title',
            'product_name',
            'status',
            'status_display',
            'priority',
            'priority_display',
            'quantity_to_produce',
            'current_progress',
            'scheduled_start_date',
            'scheduled_end_date',
            'actual_start_date',
            'is_overdue',
            'remaining_days',
            'created_at',
        ]
    
    def get_is_overdue(self, obj):
        if obj.status not in ['completed', 'archived'] and obj.scheduled_end_date:
            return timezone.now() > obj.scheduled_end_date
        return False
    
    def get_remaining_days(self, obj):
        if obj.status not in ['completed', 'archived'] and obj.scheduled_end_date:
            remaining = obj.scheduled_end_date - timezone.now()
            return max(0, remaining.days)
        return 0
    


class ProductionCardStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ProductionCard.CARD_STATUS_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        status = data.get('status')
        instance = self.instance
        
        if instance:
            # اعتبارسنجی انتقال وضعیت
            valid_transitions = {
                'draft': ['pending_approval'],
                'pending_approval': ['approved', 'draft'],
                'approved': ['in_production'],
                'in_production': ['paused', 'completed'],
                'paused': ['in_production'],
            }
            
            current_status = instance.status
            if current_status in valid_transitions and status not in valid_transitions[current_status]:
                raise serializers.ValidationError({
                    'status': f'انتقال از وضعیت {current_status} به {status} مجاز نیست'
                })
        
        return data


class ProductionCardProgressUpdateSerializer(serializers.Serializer):
    progress = serializers.IntegerField(min_value=0, max_value=100)
    notes = serializers.CharField(required=False, allow_blank=True)
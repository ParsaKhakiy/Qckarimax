# serializers.py
from rest_framework import serializers
from django.utils import timezone
from .models import (
    QualityControlExpert,
    QCHistoryCreator,
    InspectionLog,
    ProductionCard,
    ProductionCardQCInspection
)

import random 

class QualityControlExpertInputSerializer(serializers.ModelSerializer):
    """Serializer برای ایجاد و ویرایش کارشناس QC"""
    
    class Meta:
        model = QualityControlExpert
        fields = [
            'employee_code',
            'department',
            'qualification_level',
            'specialization',
            'is_active'
        ]
        read_only_fields = ['created_at', 'inspected_products_count', 'approval_rate']
    
    def validate_employee_code(self, value):
        """اعتبارسنجی کد پرسنلی"""
        # بررسی یکتایی
        if QualityControlExpert.objects.filter(employee_code=value).exists():
            if self.instance and self.instance.employee_code == value:
                return value
            raise serializers.ValidationError("این کد پرسنلی قبلاً ثبت شده است.")
        
        # فرمت کد پرسنلی (مثال: QC-001)
        if not value.startswith('QC-'):
            raise serializers.ValidationError("کد پرسنلی باید با QC- شروع شود.")
        
        return value
    
    def validate_qualification_level(self, value):
        """اعتبارسنجی سطح صلاحیت"""
        valid_levels = [choice[0] for choice in QualityControlExpert.QUALIFICATION_LEVELS]
        if value not in valid_levels:
            raise serializers.ValidationError(f"سطح صلاحیت نامعتبر. سطوح مجاز: {valid_levels}")
        return value
    
    def create(self, validated_data):
        """ایجاد کارشناس QC"""
        user = self.context['request'].user
        validated_data['user'] = user
        
        # تنظیم آمار اولیه
        validated_data['inspected_products_count'] = 0
        validated_data['approval_rate'] = 100.00
        
        return super().create(validated_data)


class QualityControlExpertOutputSerializer(serializers.ModelSerializer):
    """Serializer برای نمایش اطلاعات کارشناس QC"""
    
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    
    qualification_level_display = serializers.CharField(
        source='get_qualification_level_display',
        read_only=True
    )
    
    # آمار عملکرد
    performance_stats = serializers.SerializerMethodField(read_only=True)
    
    # اطلاعات تماس (اگر در مدل User موجود باشد)
    phone_number = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = QualityControlExpert
        fields = [
            'id',
            'user_id',
            'full_name',
            'username',
            'email',
            'employee_code',
            'department',
            'qualification_level',
            'qualification_level_display',
            'specialization',
            'inspected_products_count',
            'approval_rate',
            'performance_stats',
            'phone_number',
            'created_at',
            'is_active'
        ]
        read_only_fields = fields
    
    def get_performance_stats(self, obj):
        """محاسبه آمار عملکرد"""
        return {
            'total_inspections': obj.inspected_products_count,
            'approval_rate': float(obj.approval_rate),
            'performance_level': self._calculate_performance_level(obj.approval_rate)
        }
    
    def get_phone_number(self, obj):
        """دریافت شماره تلفن از پروفایل کاربر"""
        if hasattr(obj.user, 'profile') and hasattr(obj.user.profile, 'phone_number'):
            return obj.user.profile.phone_number
        return None
    
    def _calculate_performance_level(self, approval_rate):
        """تعیین سطح عملکرد"""
        if approval_rate >= 95:
            return 'عالی'
        elif approval_rate >= 85:
            return 'خوب'
        elif approval_rate >= 70:
            return 'متوسط'
        else:
            return 'نیاز به بهبود'


class QCHistoryCreatorOutputSerializer(serializers.ModelSerializer):
    """Serializer برای نمایش تاریخچه QC"""
    
    qc_expert_name = serializers.CharField(source='qc_expert.user.get_full_name', read_only=True)
    qc_expert_code = serializers.CharField(source='qc_expert.employee_code', read_only=True)
    
    # آمار بازرسی‌ها
    inspection_stats = serializers.SerializerMethodField(read_only=True)
    
    # لیست سفارش‌های بازرسی شده (فقط IDها)
    inspected_order_ids = serializers.SerializerMethodField(read_only=True)
    
    # لیست کارت‌های بازرسی شده
    inspected_cards = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = QCHistoryCreator
        fields = [
            'id',
            'qc_expert_name',
            'qc_expert_code',
            'inspection_stats',
            'inspected_order_ids',
            'inspected_cards',
            'created_at'
        ]
        read_only_fields = fields
    
    def get_inspection_stats(self, obj):
        """آمار بازرسی‌ها"""
        logs = obj.inspection_logs.all()
        total = logs.count()
        approved = logs.filter(status='approved').count()
        rejected = logs.filter(status='rejected').count()
        
        return {
            'total_inspections': total,
            'approved': approved,
            'rejected': rejected,
            'approval_rate': (approved / total * 100) if total > 0 else 0
        }
    
    def get_inspected_order_ids(self, obj):
        """ID سفارش‌های بازرسی شده"""
        return list(obj.inspected_orders.values_list('id', flat=True))
    
    def get_inspected_cards(self, obj):
        """اطلاعات کارت‌های بازرسی شده"""
        cards = obj.inspected_cart.all()
        return [
            {
                'card_code': card.card_code,
                'title': card.title,
                'status': card.get_status_display(),
                'inspection_date': card.created_at
            }
            for card in cards[:10]  # فقط 10 مورد اول
        ]


class InspectionLogInputSerializer(serializers.ModelSerializer):
    """Serializer برای ایجاد و ویرایش لاگ بازرسی"""
    
    class Meta:
        model = InspectionLog
        fields = [
            'order',
            'status',
            'comments',
            'rejection_reason',
            'corrected'
        ]
        read_only_fields = ['inspector', 'inspection_date', 'correction_date']
    
    def validate(self, data):
        """اعتبارسنجی یکپارچه"""
        # اگر وضعیت 'rejected' است، دلیل رد الزامی است
        if data.get('status') == 'rejected' and not data.get('rejection_reason'):
            raise serializers.ValidationError({
                'rejection_reason': 'در صورت رد بازرسی، دلیل رد الزامی است.'
            })
        
        # اگر وضعیت 'need_correction' است، corrected باید False باشد
        if data.get('status') == 'need_correction' and data.get('corrected', False):
            raise serializers.ValidationError({
                'corrected': 'برای وضعیت "نیاز به اصلاح"، مقدار corrected باید False باشد.'
            })
        
        return data
    
    def create(self, validated_data):
        """ایجاد لاگ بازرسی"""
        request = self.context.get('request')
        
        # تنظیم بازرس از context
        if request and hasattr(request, 'qc_profile'):
            validated_data['inspector'] = request.qc_profile
        else:
            raise serializers.ValidationError("بازرس QC مشخص نشده است.")
        
        # تنظیم تاریخ بازرسی
        validated_data['inspection_date'] = timezone.now()
        
        return super().create(validated_data)


class InspectionLogOutputSerializer(serializers.ModelSerializer):
    """Serializer برای نمایش لاگ بازرسی"""
    
    inspector_name = serializers.CharField(source='inspector.user.get_full_name', read_only=True)
    inspector_code = serializers.CharField(source='inspector.employee_code', read_only=True)
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # اطلاعات سفارش
    order_info = serializers.SerializerMethodField(read_only=True)
    
    # زمان‌ها
    inspection_time = serializers.SerializerMethodField(read_only=True)
    correction_time = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = InspectionLog
        fields = [
            'id',
            'inspector_name',
            'inspector_code',
            'order_id',
            'order_info',
            'status',
            'status_display',
            'comments',
            'rejection_reason',
            'corrected',
            'inspection_date',
            'inspection_time',
            'correction_date',
            'correction_time'
        ]
        read_only_fields = fields
    
    def get_order_info(self, obj):
        """اطلاعات سفارش مرتبط"""
        order = obj.order
        return {
            'customer': order.customer_name if hasattr(order, 'customer_name') else 'نامشخص',
            'total_amount': str(order.total_amount) if hasattr(order, 'total_amount') else '0',
            'order_date': order.created_at if hasattr(order, 'created_at') else None
        }
    
    def get_inspection_time(self, obj):
        """زمان بازرسی به فرمت خوانا"""
        if obj.inspection_date:
            return obj.inspection_date.strftime('%Y/%m/%d %H:%M')
        return None
    
    def get_correction_time(self, obj):
        """زمان اصلاح به فرمت خوانا"""
        if obj.correction_date:
            return obj.correction_date.strftime('%Y/%m/%d %H:%M')
        return None


class ProductionCardInputSerializer(serializers.ModelSerializer):
    """Serializer برای ایجاد و ویرایش کارت تولید"""
    
    class Meta:
        model = ProductionCard
        fields = [
            'title',
            'requirements_product',
            'priority',
            'quantity_to_produce',
            'estimated_duration',
            'scheduled_start_date',
            'scheduled_end_date',
            'required_materials',
            'required_components',
            'required_tools',
            'production_standards',
            'special_instructions',
            'qc_required',
            'qc_checkpoints',
            'notes',
            'is_active'
        ]
        read_only_fields = [
            'card_code', 
            'status', 
            'current_progress',
            'actual_start_date',
            'actual_end_date',
            'approval_date',
            'attachments',
            'created_by',
            'created_at',
            'updated_at'
        ]
    
    def validate_requirements_product(self, value):
        """اعتبارسنجی محصول و الزامات"""
        # بررسی اینکه محصول فعال باشد
        if not value.product.is_active:
            raise serializers.ValidationError("محصول مورد نظر غیرفعال است.")
        return value
    
    def validate_estimated_duration(self, value):
        """اعتبارسنجی مدت زمان تخمینی"""
        if value and value.total_seconds() <= 0:
            raise serializers.ValidationError("مدت زمان تخمینی باید مثبت باشد.")
        return value
    
    def validate_scheduled_start_date(self, value):
        """اعتبارسنجی تاریخ شروع برنامه‌ریزی شده"""
        if value and value < timezone.now():
            raise serializers.ValidationError("تاریخ شروع نمی‌تواند در گذشته باشد.")
        return value
    
    def validate_scheduled_end_date(self, value):
        """اعتبارسنجی تاریخ پایان برنامه‌ریزی شده"""
        start_date = self.initial_data.get('scheduled_start_date')
        if start_date and value:
            start_date = timezone.datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if value <= start_date:
                raise serializers.ValidationError("تاریخ پایان باید بعد از تاریخ شروع باشد.")
        return value
    
    def validate_required_materials(self, value):
        """اعتبارسنجی مواد اولیه"""
        for material in value:
            if not material.get('name') or not material.get('quantity'):
                raise serializers.ValidationError("هر ماده اولیه باید دارای نام و مقدار باشد.")
        return value
    
    def create(self, validated_data):
        """ایجاد کارت تولید"""
        request = self.context.get('request')
        
        # تنظیم کد کارت تولید
        validated_data['card_code'] = self._generate_card_code()
        
        # تنظیم ایجادکننده
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        
        # تنظیم وضعیت اولیه
        validated_data['status'] = 'draft'
        
        return super().create(validated_data)
    
    def _generate_card_code(self):
        """تولید کد کارت تولید"""
        prefix = "PC"
        timestamp = timezone.now().strftime("%y%m%d%H%M%S")
        random_num = str(random.randint(100, 999))
        return f"{prefix}-{timestamp}-{random_num}"


class ProductionCardOutputSerializer(serializers.ModelSerializer):
    """Serializer برای نمایش کارت تولید"""
    
    # اطلاعات اصلی
    requirements_product_name = serializers.CharField(
        source='requirements_product.product.name',
        read_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    # اطلاعات تولید
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    # وضعیت QC
    qc_status = serializers.SerializerMethodField(read_only=True)
    approved_by_names = serializers.SerializerMethodField(read_only=True)
    
    # زمان‌ها به فرمت خوانا
    scheduled_start = serializers.SerializerMethodField(read_only=True)
    scheduled_end = serializers.SerializerMethodField(read_only=True)
    actual_start = serializers.SerializerMethodField(read_only=True)
    actual_end = serializers.SerializerMethodField(read_only=True)
    created_at_formatted = serializers.SerializerMethodField(read_only=True)
    
    # اطلاعات مرتبط
    qc_inspections_count = serializers.SerializerMethodField(read_only=True)
    production_line_info = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = ProductionCard
        fields = [
            'id',
            'card_code',
            'title',
            'requirements_product',
            'requirements_product_name',
            'status',
            'status_display',
            'priority',
            'priority_display',
            'quantity_to_produce',
            'estimated_duration',
            'scheduled_start_date',
            'scheduled_start',
            'scheduled_end_date',
            'scheduled_end',
            'actual_start_date',
            'actual_start',
            'actual_end_date',
            'actual_end',
            'current_progress',
            'required_materials',
            'required_components',
            'required_tools',
            'production_standards',
            'special_instructions',
            'qc_required',
            'qc_checkpoints',
            'qc_status',
            'approved_by_names',
            'approval_date',
            'attachments',
            'notes',
            'is_active',
            'created_by',
            'created_by_name',
            'created_at',
            'created_at_formatted',
            'updated_at',
            'qc_inspections_count',
            'production_line_info'
        ]
        read_only_fields = fields
    
    def get_qc_status(self, obj):
        """وضعیت QC کارت تولید"""
        inspections = obj.qc_inspections.all()
        
        if not inspections.exists():
            return 'no_inspection'
        
        approved_count = inspections.filter(status='approved').count()
        pending_count = inspections.filter(status__in=['pending', 'in_progress']).count()
        rejected_count = inspections.filter(status='rejected').count()
        
        if rejected_count > 0:
            return 'rejected'
        elif pending_count > 0:
            return 'pending'
        elif approved_count == inspections.count():
            return 'fully_approved'
        else:
            return 'partial_approved'
    
    def get_approved_by_names(self, obj):
        """نام کارشناسان QC که تأیید کرده‌اند"""
        return [
            {
                'name': qc.user.get_full_name(),
                'code': qc.employee_code,
                'level': qc.get_qualification_level_display()
            }
            for qc in obj.approved_by_qa.all()
        ]
    
    def get_scheduled_start(self, obj):
        if obj.scheduled_start_date:
            return obj.scheduled_start_date.strftime('%Y/%m/%d %H:%M')
        return None
    
    def get_scheduled_end(self, obj):
        if obj.scheduled_end_date:
            return obj.scheduled_end_date.strftime('%Y/%m/%d %H:%M')
        return None
    
    def get_actual_start(self, obj):
        if obj.actual_start_date:
            return obj.actual_start_date.strftime('%Y/%m/%d %H:%M')
        return None
    
    def get_actual_end(self, obj):
        if obj.actual_end_date:
            return obj.actual_end_date.strftime('%Y/%m/%d %H:%M')
        return None
    
    def get_created_at_formatted(self, obj):
        if obj.created_at:
            return obj.created_at.strftime('%Y/%m/%d %H:%M')
        return None
    
    def get_qc_inspections_count(self, obj):
        return obj.qc_inspections.count()
    
    def get_production_line_info(self, obj):
        """اطلاعات خط تولید مرتبط"""
        # اگر ProductionCard به ProductionLine متصل باشد
        if hasattr(obj, 'production_line') and obj.production_line:
            return {
                'name': obj.production_line.name,
                'location': obj.production_line.location,
                'capacity': obj.production_line.capacity
            }
        return None


class ProductionCardQCInspectionInputSerializer(serializers.ModelSerializer):
    """Serializer برای ایجاد و ویرایش بازرسی QC کارت تولید"""
    
    class Meta:
        model = ProductionCardQCInspection
        fields = [
            'production_card',
            'inspection_type',
            'scheduled_date',
            'checklist_items',
            'test_results',
            'measurements',
            'inspector_comments',
            'rejection_reason',
            'correction_instructions',
            'needs_correction',
            'corrected'
        ]
        read_only_fields = [
            'inspection_code',
            'status',
            'actual_start_date',
            'actual_end_date',
            'overall_score',
            'passed_items',
            'failed_items',
            'total_items_checked',
            'photos',
            'inspection_report',
            'approved_by_qc_manager',
            'correction_date',
            'created_at',
            'updated_at'
        ]
    
    def validate_production_card(self, value):
        """اعتبارسنجی کارت تولید"""
        # بررسی اینکه کارت تولید فعال باشد
        if not value.is_active:
            raise serializers.ValidationError("کارت تولید مورد نظر غیرفعال است.")
        
        # بررسی وضعیت کارت تولید
        if value.status not in ['approved', 'in_production']:
            raise serializers.ValidationError(
                f"کارت تولید باید در وضعیت 'تأیید شده' یا 'در حال تولید' باشد. وضعیت فعلی: {value.get_status_display()}"
            )
        
        return value
    
    def validate_scheduled_date(self, value):
        """اعتبارسنجی تاریخ برنامه‌ریزی شده"""
        if value and value < timezone.now():
            raise serializers.ValidationError("تاریخ بازرسی نمی‌تواند در گذشته باشد.")
        return value
    
    def validate_checklist_items(self, value):
        """اعتبارسنجی اقلام چک لیست"""
        for item in value:
            if not item.get('item_name'):
                raise serializers.ValidationError("هر آیتم چک لیست باید دارای نام باشد.")
        return value
    
    def create(self, validated_data):
        """ایجاد بازرسی QC"""
        request = self.context.get('request')
        
        # تنظیم بازرس
        if request and hasattr(request, 'qc_profile'):
            validated_data['inspector'] = request.qc_profile
        else:
            raise serializers.ValidationError("بازرس QC مشخص نشده است.")
        
        # تنظیم وضعیت اولیه
        validated_data['status'] = 'pending'
        
        return super().create(validated_data)


class ProductionCardQCInspectionOutputSerializer(serializers.ModelSerializer):
    """Serializer برای نمایش بازرسی QC کارت تولید"""
    
    # اطلاعات اصلی
    inspection_code_display = serializers.SerializerMethodField(read_only=True)
    inspection_type_display = serializers.CharField(
        source='get_inspection_type_display',
        read_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # اطلاعات بازرس
    inspector_name = serializers.CharField(source='inspector.user.get_full_name', read_only=True)
    inspector_code = serializers.CharField(source='inspector.employee_code', read_only=True)
    inspector_level = serializers.CharField(
        source='inspector.get_qualification_level_display',
        read_only=True
    )
    
    # اطلاعات کارت تولید
    production_card_info = serializers.SerializerMethodField(read_only=True)
    
    # اطلاعات مدیر تأییدکننده
    approved_by_manager_name = serializers.SerializerMethodField(read_only=True)
    
    # زمان‌ها به فرمت خوانا
    scheduled_date_formatted = serializers.SerializerMethodField(read_only=True)
    actual_start_formatted = serializers.SerializerMethodField(read_only=True)
    actual_end_formatted = serializers.SerializerMethodField(read_only=True)
    created_at_formatted = serializers.SerializerMethodField(read_only=True)
    correction_date_formatted = serializers.SerializerMethodField(read_only=True)
    
    # آمار بازرسی
    inspection_stats = serializers.SerializerMethodField(read_only=True)
    
    # فایل‌ها
    report_url = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = ProductionCardQCInspection
        fields = [
            'id',
            'inspection_code',
            'inspection_code_display',
            'production_card',
            'production_card_info',
            'inspector',
            'inspector_name',
            'inspector_code',
            'inspector_level',
            'inspection_type',
            'inspection_type_display',
            'status',
            'status_display',
            'scheduled_date',
            'scheduled_date_formatted',
            'actual_start_date',
            'actual_start_formatted',
            'actual_end_date',
            'actual_end_formatted',
            'overall_score',
            'passed_items',
            'failed_items',
            'total_items_checked',
            'checklist_items',
            'test_results',
            'measurements',
            'photos',
            'inspection_report',
            'report_url',
            'inspector_comments',
            'rejection_reason',
            'correction_instructions',
            'approved_by_qc_manager',
            'approved_by_manager_name',
            'needs_correction',
            'corrected',
            'correction_date',
            'correction_date_formatted',
            'inspection_stats',
            'created_at',
            'created_at_formatted',
            'updated_at'
        ]
        read_only_fields = fields
    
    def get_inspection_code_display(self, obj):
        """نمایش زیبای کد بازرسی"""
        return f"بازرسی #{obj.inspection_code}"
    
    def get_production_card_info(self, obj):
        """اطلاعات کارت تولید"""
        return {
            'card_code': obj.production_card.card_code,
            'title': obj.production_card.title,
            'status': obj.production_card.get_status_display(),
            'priority': obj.production_card.get_priority_display()
        }
    
    def get_approved_by_manager_name(self, obj):
        """نام مدیر تأییدکننده"""
        if obj.approved_by_qc_manager:
            return obj.approved_by_qc_manager.user.get_full_name()
        return None
    
    def get_scheduled_date_formatted(self, obj):
        if obj.scheduled_date:
            return obj.scheduled_date.strftime('%Y/%m/%d %H:%M')
        return None
    
    def get_actual_start_formatted(self, obj):
        if obj.actual_start_date:
            return obj.actual_start_date.strftime('%Y/%m/%d %H:%M')
        return None
    
    def get_actual_end_formatted(self, obj):
        if obj.actual_end_date:
            return obj.actual_end_date.strftime('%Y/%m/%d %H:%M')
        return None
    
    def get_created_at_formatted(self, obj):
        if obj.created_at:
            return obj.created_at.strftime('%Y/%m/%d %H:%M')
        return None
    
    def get_correction_date_formatted(self, obj):
        if obj.correction_date:
            return obj.correction_date.strftime('%Y/%m/%d %H:%M')
        return None
    
    def get_inspection_stats(self, obj):
        """آمار بازرسی"""
        return {
            'total_items': obj.total_items_checked,
            'passed_rate': (obj.passed_items / obj.total_items_checked * 100) if obj.total_items_checked > 0 else 0,
            'failed_rate': (obj.failed_items / obj.total_items_checked * 100) if obj.total_items_checked > 0 else 0,
            'overall_score': float(obj.overall_score) if obj.overall_score else 0,
            'completion_status': 'کامل' if obj.actual_end_date else 'در جریان'
        }
    
    def get_report_url(self, obj):
        """آدرس گزارش بازرسی"""
        if obj.inspection_report:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.inspection_report.url)
        return None
    

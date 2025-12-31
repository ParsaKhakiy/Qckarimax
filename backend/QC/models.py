

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

import random
from time import timezone


class QualityControlExpert(models.Model):
    """مدل کارشناس کنترل کیفیت"""
    
    # اتصال به یوزر سیستم
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='qc_profile',
        verbose_name="کاربر سیستم"
    )
    
    employee_code = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name="کد پرسنلی"
    )
    
    department = models.CharField(
        max_length=100, 
        verbose_name="بخش/واحد کنترل کیفیت"
    )
    
    QUALIFICATION_LEVELS = [
        ('basic', 'کارشناس پایه'),
        ('senior', 'کارشناس ارشد'),
        ('supervisor', 'سرپرست'),
        ('manager', 'مدیر کنترل کیفیت'),
    ]
    
    qualification_level = models.CharField(
        max_length=20,
        choices=QUALIFICATION_LEVELS,
        default='basic',
        verbose_name="سطح صلاحیت"
    )
    
    specialization = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="تخصص ویژه"
    )
    
    inspected_products_count = models.PositiveIntegerField(
        default=0,
        verbose_name="تعداد محصولات بازرسی شده"
    )
    
    approval_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=100.00,
        verbose_name="نرخ تایید (%)"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ عضویت"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )
    
    class Meta:
        verbose_name = "کارشناس کنترل کیفیت"
        verbose_name_plural = "کارشناسان کنترل کیفیت"
        ordering = ['-qualification_level', 'user__last_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.employee_code} - {self.department}"
    
    def update_inspection_stats(self, approved_count, total_inspected):
        """به روزرسانی آمار بازرسی"""
        if total_inspected > 0:
            self.inspected_products_count += total_inspected
            self.approval_rate = (approved_count / total_inspected) * 100
            self.save()





class QCHistoryCreator(models.Model):
    """مدل برای ثبت تاریخچه بازرسی‌های QC"""
    
    qc_expert = models.OneToOneField(
        QualityControlExpert, 
        on_delete=models.DO_NOTHING,
        related_name='qc_history',
        verbose_name="کارشناس کنترل کیفیت"
    )
    
    inspected_orders = models.ManyToManyField(
        'order.Order',
        related_name='QC_inspections',
        verbose_name="سفارش‌های بازرسی شده",
        blank=True
    )
    
    inspection_logs = models.ManyToManyField(
        'QC.InspectionLog',
        related_name='qc_expert_logs',
        verbose_name="لاگ‌های بازرسی",
        blank=True
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )
    
    class Meta:
        verbose_name = "تاریخچه بازرسی QC"
        verbose_name_plural = "تاریخچه‌های بازرسی QC"
    
    def __str__(self):
        return f"تاریخچه بازرسی‌های {self.qc_expert.user.get_full_name()}"



class InspectionLog(models.Model):
    """مدل برای ثبت جزئیات هر بازرسی"""
    
    INSPECTION_STATUS = [
        ('pending', 'در انتظار'),
        ('in_progress', 'در حال بازرسی'),
        ('approved', 'تایید شده'),
        ('rejected', 'رد شده'),
        ('need_correction', 'نیاز به اصلاح'),
    ]
    
    inspector = models.ForeignKey(
        QualityControlExpert,
        on_delete=models.SET_NULL,
        null=True,
        related_name='inspection_records',
        verbose_name="بازرس"
    )
    
    order = models.ForeignKey(
        'order.Order',
        on_delete=models.CASCADE,
        related_name='qc_logs',
        verbose_name="سفارش"
    )
    
    status = models.CharField(
        max_length=20,
        choices=INSPECTION_STATUS,
        default='pending',
        verbose_name="وضعیت بازرسی"
    )
    
    inspection_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ بازرسی"
    )
    
    comments = models.TextField(
        blank=True,
        null=True,
        verbose_name="توضیحات بازرس"
    )
    
    rejection_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name="دلیل رد (در صورت وجود)"
    )
    
    corrected = models.BooleanField(
        default=False,
        verbose_name="اصلاح شده"
    )
    
    correction_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="تاریخ اصلاح"
    )
    
    class Meta:
        verbose_name = "لاگ بازرسی"
        verbose_name_plural = "لاگ‌های بازرسی"
        ordering = ['-inspection_date']
    
    def __str__(self):
        return f"بازرسی سفارش {self.order.id} توسط {self.inspector}"



class QCStandard(models.Model):
    """مدل برای استانداردهای کنترل کیفیت"""
    
    name = models.CharField(
        max_length=200,
        verbose_name="نام استاندارد"
    )
    
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="کد استاندارد"
    )
    
    description = models.TextField(
        verbose_name="توضیحات استاندارد"
    )
    
    category = models.CharField(
        max_length=100,
        verbose_name="دسته‌بندی"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )
    
    created_by = models.ForeignKey(
        QualityControlExpert,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="ایجاد شده توسط"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی"
    )
    
    class Meta:
        verbose_name = "استاندارد QC"
        verbose_name_plural = "استانداردهای QC"
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
#########


class ProductionCard(models.Model):
    """مدل کارت تولید برای هر محصول"""
    
    CARD_STATUS_CHOICES = (
        ('draft', 'پیش‌نویس'),
        ('pending_approval', 'در انتظار تأیید'),
        ('approved', 'تأیید شده'),
        ('in_production', 'در حال تولید'),
        ('paused', 'متوقف شده'),
        ('completed', 'تکمیل شده'),
        ('archived', 'آرشیو شده'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'کم'),
        ('medium', 'متوسط'),
        ('high', 'بالا'),
        ('urgent', 'فوری'),
    )
    
    # اطلاعات اصلی
    card_code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="کد کارت تولید"
    )
    
    title = models.CharField(
        max_length=255,
        verbose_name="عنوان کارت تولید"
    )
    
    requirements_product = models.ForeignKey(
        'product.RequirementsProducts',
        on_delete=models.CASCADE,
        related_name='production_cards',
        verbose_name="محصول و الزامات مرتبط"
    )
    
    # وضعیت و اولویت
    status = models.CharField(
        max_length=20,
        choices=CARD_STATUS_CHOICES,
        default='draft',
        verbose_name="وضعیت کارت"
    )
    
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name="اولویت تولید"
    )
    
    # اطلاعات تولید
    quantity_to_produce = models.PositiveIntegerField(
        default=1,
        verbose_name="تعداد مورد نیاز"
    )
    

    
    # زمان‌بندی
    estimated_duration = models.DurationField(
        null=True,
        blank=True,
        verbose_name="زمان تخمینی تولید (ساعت)"
    )
    
    scheduled_start_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="زمان شروع برنامه‌ریزی شده"
    )
    
    scheduled_end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="زمان پایان برنامه‌ریزی شده"
    )
    
    actual_start_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="زمان شروع واقعی"
    )
    
    actual_end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="زمان پایان واقعی"
    )
    
    # پیگیری و کنترل
    current_progress = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="درصد پیشرفت (%)"
    )
    

    
    # مواد اولیه و قطعات
    required_materials = models.JSONField(
        default=list,
        blank=True,
        verbose_name="لیست مواد اولیه مورد نیاز"
    )
    
    required_components = models.JSONField(
        default=list,
        blank=True,
        verbose_name="لیست قطعات مورد نیاز"
    )
    
    # ابزار و تجهیزات
    required_tools = models.JSONField(
        default=list,
        blank=True,
        verbose_name="لیست ابزار مورد نیاز"
    )
    
    # استانداردها و دستورالعمل‌ها
    production_standards = models.TextField(
        blank=True,
        verbose_name="استانداردهای تولید"
    )
    
    special_instructions = models.TextField(
        blank=True,
        verbose_name="دستورالعمل‌های ویژه"
    )
    
    # کنترل کیفیت
    qc_required = models.BooleanField(
        default=True,
        verbose_name="نیاز به کنترل کیفیت دارد"
    )
    
    qc_checkpoints = models.PositiveIntegerField(
        default=1,
        verbose_name="تعداد نقاط کنترل کیفیت"
    )
    

    approved_by_qa = models.ForeignKey( # must related to the qc 
        QualityControlExpert,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='qa_approved_production_cards',
        verbose_name="تأیید شده توسط کنترل کیفیت"
    )
    
    approval_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاریخ تأیید"
    )
    
    # پیوست‌ها و مستندات
    attachments = models.JSONField(
        default=list,
        blank=True,
        verbose_name="فایل‌های پیوست"
    )
    

    
    # مت
    notes = models.TextField(
        blank=True,
        verbose_name="یادداشت‌ها"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )
    
    created_by = models.ForeignKey(
        QualityControlExpert,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_production_cards',
        verbose_name="ایجاد کننده"
    ) 
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی"
    )
    
    class Meta:
        verbose_name = "کارت تولید"
        verbose_name_plural = "کارت‌های تولید"
        ordering = ['-priority', 'scheduled_start_date']
        indexes = [
            models.Index(fields=['card_code']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['scheduled_start_date']),
        ]
    
    def __str__(self):
        return f"{self.card_code} - {self.title}"
    
    def save(self, *args, **kwargs):
        # ایجاد کد کارت تولید به صورت خودکار اگر وجود ندارد
        if not self.card_code:
            product_name = self.requirements_product.product.name[:3].upper()
            date_part = timezone.now().strftime("%y%m%d")
            random_part = str(random.randint(100, 999))
            self.card_code = f"PC-{product_name}-{date_part}-{random_part}"
        
        super().save(*args, **kwargs)
    
    @property
    def product(self):
        """دسترسی آسان به محصول مرتبط"""
        return self.requirements_product.product
    
    @property
    def requirements_list(self):
        """لیست الزامات مرتبط"""
        return self.requirements_product.requirements.all()
    
    @property
    def is_on_schedule(self):
        """بررسی آیا تولید در زمان برنامه‌ریزی شده است"""
        if not self.actual_start_date or not self.scheduled_start_date:
            return None
        
        time_diff = self.actual_start_date - self.scheduled_start_date
        return abs(time_diff.total_seconds()) < 3600  # تفاوت کمتر از 1 ساعت
    
    @property
    def production_duration(self):
        """محاسبه مدت زمان تولید"""
        if self.actual_start_date and self.actual_end_date:
            return self.actual_end_date - self.actual_start_date
        return None
    
    def update_progress(self, new_progress):
        """به‌روزرسانی درصد پیشرفت"""
        if 0 <= new_progress <= 100:
            self.current_progress = new_progress
            self.save()
    
    def assign_operator(self, operator):
        """اختصاص اپراتور به کارت تولید"""
        self.assigned_operators.add(operator)
    
    def add_production_step(self, step_name, description, duration, tools=None):
        """افزودن مرحله تولید"""
        step = {
            'name': step_name,
            'description': description,
            'duration': str(duration),
            'tools': tools or [],
            'added_at': timezone.now().isoformat(),
            'completed': False,
            'completed_at': None
        }
        self.production_steps.append(step)
        self.save()
    
    def complete_step(self, step_index, notes=None):
        """تکمیل یک مرحله تولید"""
        if step_index < len(self.production_steps):
            self.production_steps[step_index]['completed'] = True
            self.production_steps[step_index]['completed_at'] = timezone.now().isoformat()
            if notes:
                self.production_steps[step_index]['notes'] = notes
            self.save()
    
    def add_quality_checkpoint(self, checkpoint_name, standard, required_action):
        """افزودن نقطه کنترل کیفیت"""
        checkpoint = {
            'name': checkpoint_name,
            'standard': standard,
            'required_action': required_action,
            'checked': False,
            'checked_by': None,
            'checked_at': None,
            'result': None
        }
        self.quality_checkpoints.append(checkpoint)
        self.save()


class ProductionCardLog(models.Model):
    """مدل برای ثبت لاگ تغییرات کارت تولید"""
    
    LOG_TYPES = (
        ('status_change', 'تغییر وضعیت'),
        ('progress_update', 'به‌روزرسانی پیشرفت'),
        ('operator_assignment', 'اختصاص اپراتور'),
        ('material_usage', 'مصرف مواد'),
        ('quality_check', 'کنترل کیفیت'),
        ('note_added', 'افزودن یادداشت'),
        ('file_uploaded', 'آپلود فایل'),
        ('time_adjustment', 'تغییر زمان'),
    )
    
    production_card = models.ForeignKey(
        'ProductionCard',
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name="کارت تولید"
    )
    
    log_type = models.CharField(
        max_length=20,
        choices=LOG_TYPES,
        verbose_name="نوع رویداد"
    )
    
    description = models.TextField(
        verbose_name="توضیحات رویداد"
    )
    
    old_value = models.TextField(
        blank=True,
        null=True,
        verbose_name="مقدار قبلی"
    )
    
    new_value = models.TextField(
        blank=True,
        null=True,
        verbose_name="مقدار جدید"
    )
    
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="انجام شده توسط"
    )
    
    performed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان انجام"
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="اطلاعات اضافی"
    )
    
    class Meta:
        verbose_name = "لاگ کارت تولید"
        verbose_name_plural = "لاگ‌های کارت تولید"
        ordering = ['-performed_at']
        indexes = [
            models.Index(fields=['production_card', 'performed_at']),
            models.Index(fields=['log_type']),
        ]
    
    def __str__(self):
        return f"لاگ {self.log_type} برای کارت {self.production_card.card_code}"


class MaterialConsumption(models.Model):
    """مدل برای پیگیری مصرف مواد اولیه در هر کارت تولید"""
    
    production_card = models.ForeignKey(
        'ProductionCard',
        on_delete=models.CASCADE,
        related_name='material_consumptions',
        verbose_name="کارت تولید"
    )
    
    material_name = models.CharField(
        max_length=200,
        verbose_name="نام ماده اولیه"
    )
    
    material_code = models.CharField(
        max_length=50,
        verbose_name="کد ماده"
    )
    
    unit = models.CharField(
        max_length=20,
        verbose_name="واحد اندازه‌گیری"
    )
    
    estimated_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="مقدار تخمینی"
    )
    
    actual_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="مقدار مصرف واقعی"
    )
    
    consumption_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاریخ مصرف"
    )
    
    consumed_by = models.ForeignKey(
        'product.Operator',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="مصرف شده توسط"
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name="یادداشت‌ها"
    )
    
    class Meta:
        verbose_name = "مصرف مواد اولیه"
        verbose_name_plural = "مصرف مواد اولیه"
    
    def __str__(self):
        return f"{self.material_name} - کارت {self.production_card.card_code}"
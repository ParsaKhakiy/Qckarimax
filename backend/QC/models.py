

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
    
    inspected_products_count = models.PositiveIntegerField( # 
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
    inspected_cart = models.ManyToManyField(
        'ProductionCard'  , 
        related_name='inspected_cart_p_cart'
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
    
    order = models.ForeignKey( # one to one 
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








# Cart from products 
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
    

    approved_by_qa = models.ManyToManyField( 
        QualityControlExpert,
        blank=True,
        related_name='qa_approved_production_cards',
        verbose_name="تأیید شده توسط کنترل کیفیت"
    )
    # check that Qc Can provide this sections 
    
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
    # create by qc controller 
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
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
    






class ProductionCardQCInspection(
    models.Model
    ):
    """مدل بازرسی QC برای کارت تولید"""
    
    INSPECTION_STATUS = (
        ('pending', 'در انتظار بازرسی'),
        ('in_progress', 'در حال بازرسی'),
        ('approved', 'تأیید شده'),
        ('rejected', 'رد شده'),
        ('needs_correction', 'نیاز به اصلاح'),
        ('re_inspection', 'بازرسی مجدد'),
    )
    
    INSPECTION_TYPE = (
        ('initial', 'بازرسی اولیه'),
        ('in_process', 'بازرسی حین تولید'),
        ('final', 'بازرسی نهایی'),
        ('random', 'بازرسی تصادفی'),
        ('special', 'بازرسی ویژه'),
    )
    
    # ارتباط با کارت تولید
    production_card = models.ForeignKey(
        'ProductionCard',
        on_delete=models.CASCADE,
        related_name='qc_inspections',
        verbose_name="کارت تولید"
    )
    
    # بازرس QC
    inspector = models.OneToOneField(
        QualityControlExpert,
        on_delete=models.SET_NULL,
        null=True,
        related_name='card_inspections',
        verbose_name="بازرس QC"
    )
    
    # اطلاعات بازرسی
    inspection_code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="کد بازرسی"
    )
    
    inspection_type = models.CharField(
        max_length=20,
        choices=INSPECTION_TYPE,
        default='in_process',
        verbose_name="نوع بازرسی"
    )
    
    status = models.CharField(
        max_length=20,
        choices=INSPECTION_STATUS,
        default='pending',
        verbose_name="وضعیت بازرسی"
    )
    
    # زمان‌بندی
    scheduled_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="زمان برنامه‌ریزی شده بازرسی"
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
    
    # نتایج بازرسی
    overall_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="امتیاز کلی",
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    passed_items = models.PositiveIntegerField(
        default=0,
        verbose_name="تعداد موارد تأیید شده"
    )
    
    failed_items = models.PositiveIntegerField(
        default=0,
        verbose_name="تعداد موارد رد شده"
    )
    
    total_items_checked = models.PositiveIntegerField(
        default=0,
        verbose_name="تعداد کل موارد بررسی شده"
    )
    
    # جزئیات بازرسی
    checklist_items = models.JSONField(
        default=list,
        blank=True,
        verbose_name="اقلام چک لیست"
    )
    
    test_results = models.JSONField(
        default=list,
        blank=True,
        verbose_name="نتایج آزمون‌ها"
    )
    
    measurements = models.JSONField(
        default=list,
        blank=True,
        verbose_name="اندازه‌گیری‌ها"
    )
    

    # مستندات
    inspection_report = models.FileField(
        upload_to='qc_reports/production_cards/',
        null=True,
        blank=True,
        verbose_name="گزارش بازرسی"
    )
    
    photos = models.JSONField(
        default=list,
        blank=True,
        verbose_name="عکس‌های بازرسی"
    )
    
    # نظرات و توضیحات
    inspector_comments = models.TextField(
        blank=True,
        verbose_name="نظرات بازرس"
    )
    
    rejection_reason = models.TextField(
        blank=True,
        verbose_name="دلیل رد (در صورت وجود)"
    )
    
    correction_instructions = models.TextField(
        blank=True,
        verbose_name="دستورالعمل‌های اصلاح"
    )
    
    # تأییدیه‌ها
    approved_by_qc_manager = models.ForeignKey(
        QualityControlExpert,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_card_inspections',
        verbose_name="تأیید شده توسط مدیر QC"
    )
    
    # پیگیری اصلاحات
    needs_correction = models.BooleanField(
        default=False,
        verbose_name="نیاز به اصلاح دارد"
    )
    
    corrected = models.BooleanField(
        default=False,
        verbose_name="اصلاح شده"
    )
    
    correction_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاریخ اصلاح"
    )
    
    # متادیتا
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی"
    )
    
    class Meta:
        verbose_name = "بازرسی کارت تولید"
        verbose_name_plural = "بازرسی‌های کارت تولید"
        ordering = ['-scheduled_date']
        indexes = [
            models.Index(fields=['inspection_code']),
            models.Index(fields=['status']),
            models.Index(fields=['production_card', 'status']),
        ]
    
    def __str__(self):
        return f"بازرسی {self.inspection_code} - کارت {self.production_card.card_code}"
    


    
    def save(self, *args, **kwargs):
        # ایجاد کد بازرسی به صورت خودکار
        if not self.inspection_code:
            card_code = self.production_card.card_code[:5]
            date_part = timezone.now().strftime("%y%m%d%H%M")
            self.inspection_code = f"QC-{card_code}-{date_part}"
        
        # محاسبه تعداد کل موارد بررسی شده
        self.total_items_checked = self.passed_items + self.failed_items
        
        # محاسبه امتیاز کلی اگر مواردی بررسی شده باشد
        if self.total_items_checked > 0:
            self.overall_score = (self.passed_items / self.total_items_checked) * 100
        
        super().save(*args, **kwargs)
    
    def add_checklist_item(self, item_name, standard_value, actual_value, passed):
        """افزودن مورد به چک لیست"""
        item = {
            'id': len(self.checklist_items) + 1,
            'item_name': item_name,
            'standard_value': standard_value,
            'actual_value': actual_value,
            'passed': passed,
            'checked_at': timezone.now().isoformat(),
            'notes': ''
        }
        self.checklist_items.append(item)
        
        # به‌روزرسانی آمار
        if passed:
            self.passed_items += 1
        else:
            self.failed_items += 1
        
        self.save()
    

    def add_test_result(self, test_name, method, result, unit, passed):
        """افزودن نتیجه آزمون"""
        test = {
            'test_name': test_name,
            'method': method,
            'result': result,
            'unit': unit,
            'passed': passed,
            'tested_at': timezone.now().isoformat(),
            'operator': None
        }
        self.test_results.append(test)
        self.save()
    
    def approve_inspection(self, qc_manager, comments=""):
        """تأیید بازرسی توسط مدیر QC"""
        if self.status == 'approved':
            return
        
        self.status = 'approved'
        self.approved_by_qc_manager = qc_manager
        self.inspector_comments = comments
        self.save()
        
        # به‌روزرسانی وضعیت کارت تولید اگر بازرسی نهایی باشد
        if self.inspection_type == 'final' and self.status == 'approved':
            self.production_card.status = 'completed'
            self.production_card.approved_by_qa = self.inspector
            self.production_card.approval_date = timezone.now()
            self.production_card.save()
    
    def reject_inspection(self, reason, needs_correction=True):
        """رد بازرسی"""
        self.status = 'rejected'
        self.rejection_reason = reason
        self.needs_correction = needs_correction
        self.save()
        
        # به‌روزرسانی وضعیت کارت تولید
        self.production_card.status = 'paused'
        self.production_card.save()

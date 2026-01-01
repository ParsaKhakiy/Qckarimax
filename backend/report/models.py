from django.db import models
from django.utils import timezone
# Create your models here.
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class WorkStation(models.Model):
    """
    مدل ایستگاه کاری - محل‌هایی که QC می‌تونه بازرسی انجام بده
    """
    STATION_TYPES = [
        ('incoming_inspection', 'بازرسی مواد ورودی'),
        ('in_process', 'بازرسی حین فرآیند'),
        ('final_inspection', 'بازرسی نهایی'),
        ('packaging', 'بازرسی بسته‌بندی'),
        ('laboratory', 'آزمایشگاه'),
        ('calibration', 'کالیبراسیون'),
        ('warehouse', 'انبار'),
        ('shipping', 'بارگیری'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'فعال'),
        ('inactive', 'غیرفعال'),
        ('maintenance', 'در حال تعمیر'),
        ('calibration_due', 'نیاز به کالیبراسیون'),
    ]
    
    # اطلاعات اصلی
    station_code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="کد ایستگاه کاری"
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name="نام ایستگاه کاری"
    )
    
    station_type = models.CharField(
        max_length=50,
        choices=STATION_TYPES,
        verbose_name="نوع ایستگاه"
    )
    
    location = models.CharField(
        max_length=300,
        verbose_name="مکان ایستگاه"
    )
    
    department = models.CharField(
        max_length=100,
        verbose_name="دپارتمان/بخش"
    )
    
    # مسئولیت
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supervised_workstations',
        verbose_name="سرپرست ایستگاه"
    )
    
    qc_responsible = models.ForeignKey(
        'QC.QualityControlExpert',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='responsible_workstations',
        verbose_name="مسئول QC ایستگاه"
    )
    
    # تجهیزات و امکانات
    equipments = models.JSONField(
        default=list,
        blank=True,
        verbose_name="تجهیزات موجود"
    )
    
    tools = models.JSONField(
        default=list,
        blank=True,
        verbose_name="ابزارهای اندازه‌گیری"
    )

    
    # ظرفیت و برنامه
    max_daily_capacity = models.PositiveIntegerField(
        default=50,
        verbose_name="ظرفیت روزانه (تعداد بازرسی)"
    )
    
    working_hours = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="ساعات کاری"
    )
    
    # وضعیت
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="وضعیت ایستگاه"
    )
    
    is_available = models.BooleanField(
        default=True,
        verbose_name="در دسترس است"
    )
    
    # متادیتا
    description = models.TextField(
        blank=True,
        verbose_name="توضیحات"
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name="یادداشت‌ها"
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_workstations',
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
        verbose_name = "ایستگاه کاری"
        verbose_name_plural = "ایستگاه‌های کاری"
        ordering = ['department', 'station_code']
        indexes = [
            models.Index(fields=['station_code']),
            models.Index(fields=['station_type']),
            models.Index(fields=['status']),
            models.Index(fields=['department']),
        ]
    
    def __str__(self):
        return f"{self.station_code} - {self.name} ({self.get_station_type_display()})"
    
    def save(self, *args, **kwargs):
        if not self.station_code:
            # تولید کد ایستگاه
            prefix = "WS"
            dept_code = self.department[:3].upper() if self.department else "GEN"
            timestamp = timezone.now().strftime("%y%m")
            count = WorkStation.objects.filter(
                department=self.department
            ).count() + 1
            self.station_code = f"{prefix}-{dept_code}-{timestamp}-{count:03d}"
        super().save(*args, **kwargs)
    
    @property
    def today_inspections_count(self):
        """تعداد بازرسی‌های امروز"""
        today = timezone.now().date()
        return self.workstation_reports.filter(
            created_at__date=today
        ).count()
    
    @property
    def availability_status(self):
        """وضعیت دسترسی"""
        if not self.is_available:
            return 'not_available'
        if self.today_inspections_count >= self.max_daily_capacity:
            return 'at_capacity'
        return 'available'


class WorkStationReport(models.Model):
    """
    مدل گزارش‌های ثبت شده در ایستگاه‌های کاری
    """
    REPORT_TYPES = [
        ('routine_inspection', 'بازرسی معمول'),
        ('non_conformity', 'عدم انطباق'),
        ('calibration', 'کالیبراسیون'),
        ('maintenance', 'تعمیرات'),
        ('incident', 'حادثه'),
        ('audit', 'بازرسی داخلی'),
        ('improvement', 'اقدام بهبود'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'کم'),
        ('medium', 'متوسط'),
        ('high', 'بالا'),
        ('critical', 'بحرانی'),
    ]
    
    # ارتباطات
    workstation = models.ForeignKey(
        WorkStation,
        on_delete=models.CASCADE,
        related_name='workstation_reports',
        verbose_name="ایستگاه کاری"
    )
    
    reporter = models.ForeignKey(
        'QC.QualityControlExpert',
        on_delete=models.SET_NULL,
        null=True,
        related_name='workstation_reports',
        verbose_name="گزارش‌دهنده"
    )
    
    # اطلاعات گزارش
    report_code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="کد گزارش"
    )
    
    report_type = models.CharField(
        max_length=30,
        choices=REPORT_TYPES,
        verbose_name="نوع گزارش"
    )
    
    title = models.CharField(
        max_length=300,
        verbose_name="عنوان گزارش"
    )
    
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_LEVELS,
        default='medium',
        verbose_name="اولویت"
    )
    
    # محتوای گزارش
    description = models.TextField(
        verbose_name="شرح گزارش"
    )
    
    observations = models.TextField(
        blank=True,
        verbose_name="مشاهدات"
    )
    
    findings = models.JSONField(
        default=list,
        blank=True,
        verbose_name="یافته‌ها"
    )
    
    measurements = models.JSONField(
        default=list,
        blank=True,
        verbose_name="اندازه‌گیری‌ها"
    )
    
    test_results = models.JSONField(
        default=list,
        blank=True,
        verbose_name="نتایج آزمایش"
    )
    
    # مستندات
    photos = models.JSONField(
        default=list,
        blank=True,
        verbose_name="عکس‌ها"
    )
    
    documents = models.JSONField(
        default=list,
        blank=True,
        verbose_name="مستندات ضمیمه"
    )
    
    # وضعیت گزارش
    STATUS_CHOICES = [
        ('draft', 'پیش‌نویس'),
        ('submitted', 'ثبت شده'),
        ('under_review', 'در حال بررسی'),
        ('approved', 'تأیید شده'),
        ('rejected', 'رد شده'),
        ('action_required', 'نیاز به اقدام'),
        ('completed', 'تکمیل شده'),
        ('archived', 'آرشیو شده'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="وضعیت گزارش"
    )
    
    # اقدامات
    corrective_actions = models.TextField(
        blank=True,
        verbose_name="اقدامات اصلاحی"
    )
    
    preventive_actions = models.TextField(
        blank=True,
        verbose_name="اقدامات پیشگیرانه"
    )
    
    action_deadline = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="ددلاین اقدام"
    )
    
    action_responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='action_responsible_reports',
        verbose_name="مسئول اقدام"
    )
    
    # تأییدیه‌ها
    reviewed_by = models.ForeignKey(
        'QC.QualityControlExpert',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_reports',
        verbose_name="بررسی شده توسط"
    )
    
    approved_by = models.ForeignKey(
        'QC.QualityControlExpert',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_reports',
        verbose_name="تأیید شده توسط"
    )
    
    review_comments = models.TextField(
        blank=True,
        verbose_name="نظرات بررسی"
    )
    
    # زمان‌ها
    report_date = models.DateTimeField(
        default=timezone.now,
        verbose_name="تاریخ گزارش"
    )
    
    inspection_start_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="زمان شروع بازرسی"
    )
    
    inspection_end_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="زمان پایان بازرسی"
    )
    
    review_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاریخ بررسی"
    )
    
    approval_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاریخ تأیید"
    )
    
    completion_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاریخ تکمیل"
    )
    
    # ارتباط با سایر مدل‌ها
    related_production_card = models.ForeignKey(
        'QC.ProductionCard',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workstation_reports',
        verbose_name="کارت تولید مرتبط"
    )
    
    related_qc_inspection = models.ForeignKey(
        'QC.ProductionCardQCInspection',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workstation_reports',
        verbose_name="بازرسی QC مرتبط"
    )
    
    related_order = models.ForeignKey(
        'order.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workstation_reports',
        verbose_name="سفارش مرتبط"
    )
    
    # متادیتا
    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name="برچسب‌ها"
    )
    
    is_urgent = models.BooleanField(
        default=False,
        verbose_name="فوری"
    )
    
    is_confidential = models.BooleanField(
        default=False,
        verbose_name="محرمانه"
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
        verbose_name = "گزارش ایستگاه کاری"
        verbose_name_plural = "گزارش‌های ایستگاه کاری"
        ordering = ['-report_date']
        indexes = [
            models.Index(fields=['report_code']),
            models.Index(fields=['status']),
            models.Index(fields=['workstation', 'report_date']),
            models.Index(fields=['reporter', 'status']),
            models.Index(fields=['priority', 'is_urgent']),
        ]
    
    def __str__(self):
        return f"گزارش {self.report_code} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.report_code:
            # تولید کد گزارش
            ws_code = self.workstation.station_code[:5] if self.workstation else "GEN"
            timestamp = timezone.now().strftime("%y%m%d%H%M")
            count = WorkStationReport.objects.filter(
                workstation=self.workstation,
                report_date__date=timezone.now().date()
            ).count() + 1
            self.report_code = f"WSR-{ws_code}-{timestamp}-{count:03d}"
        
        # اگر وضعیت به تأیید شده تغییر کرد
        if self.status == 'approved' and not self.approval_date:
            self.approval_date = timezone.now()
        
        # اگر وضعیت به تکمیل شده تغییر کرد
        if self.status == 'completed' and not self.completion_date:
            self.completion_date = timezone.now()
        
        super().save(*args, **kwargs)
    
    def calculate_inspection_duration(self):
        """محاسبه مدت زمان بازرسی"""
        if self.inspection_start_time and self.inspection_end_time:
            duration = self.inspection_end_time - self.inspection_start_time
            return {
                'hours': duration.total_seconds() // 3600,
                'minutes': (duration.total_seconds() % 3600) // 60,
                'seconds': duration.total_seconds() % 60
            }
        return None
    
    @property
    def report_age(self):
        """سن گزارش (روز)"""
        return (timezone.now() - self.created_at).days


class WorkStationActivityLog(models.Model):
    """
    لاگ فعالیت‌های ایستگاه کاری
    """
    ACTIVITY_TYPES = [
        ('login', 'ورود به ایستگاه'),
        ('logout', 'خروج از ایستگاه'),
        ('report_created', 'ایجاد گزارش'),
        ('report_updated', 'ویرایش گزارش'),
        ('report_submitted', 'ثبت گزارش'),
        ('report_reviewed', 'بررسی گزارش'),
        ('report_approved', 'تأیید گزارش'),
        ('calibration_started', 'شروع کالیبراسیون'),
        ('calibration_completed', 'اتمام کالیبراسیون'),
        ('maintenance_started', 'شروع تعمیرات'),
        ('maintenance_completed', 'اتمام تعمیرات'),
        ('equipment_used', 'استفاده از تجهیزات'),
        ('alert_triggered', 'اعلان فعال شد'),
        ('status_changed', 'تغییر وضعیت'),
    ]
    
    workstation = models.ForeignKey(
        WorkStation,
        on_delete=models.CASCADE,
        related_name='activity_logs',
        verbose_name="ایستگاه کاری"
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="کاربر"
    )
    
    qc_expert = models.ForeignKey(
        'QC.QualityControlExpert',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="کارشناس QC"
    )
    
    activity_type = models.CharField(
        max_length=50,
        choices=ACTIVITY_TYPES,
        verbose_name="نوع فعالیت"
    )
    
    description = models.TextField(
        verbose_name="توضیحات فعالیت"
    )
    
    report = models.ForeignKey(
        WorkStationReport,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
        verbose_name="گزارش مرتبط"
    )
    
    details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="جزئیات فعالیت"
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="آدرس IP"
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان ثبت"
    )
    
    class Meta:
        verbose_name = "لاگ فعالیت ایستگاه"
        verbose_name_plural = "لاگ‌های فعالیت ایستگاه"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.workstation}"


class WorkStationAlert(models.Model):
    """
    اعلان‌های ایستگاه کاری
    """
    ALERT_TYPES = [
        ('capacity_warning', 'هشدار ظرفیت'),
        ('maintenance_due', 'تعمیرات دوره‌ای'),
        ('calibration_due', 'کالیبراسیون دوره‌ای'),
        ('equipment_failure', 'خرابی تجهیزات'),
        ('safety_issue', 'مسئله ایمنی'),
        ('quality_issue', 'مسئله کیفیت'),
        ('urgent_report', 'گزارش فوری'),
        ('deadline_approaching', 'نزدیک شدن ددلاین'),
    ]
    
    ALERT_LEVELS = [
        ('info', 'اطلاع'),
        ('warning', 'هشدار'),
        ('error', 'خطا'),
        ('critical', 'بحرانی'),
    ]
    
    workstation = models.ForeignKey(
        WorkStation,
        on_delete=models.CASCADE,
        related_name='alerts',
        verbose_name="ایستگاه کاری"
    )
    
    alert_type = models.CharField(
        max_length=50,
        choices=ALERT_TYPES,
        verbose_name="نوع اعلان"
    )
    
    alert_level = models.CharField(
        max_length=20,
        choices=ALERT_LEVELS,
        verbose_name="سطح اعلان"
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name="عنوان اعلان"
    )
    
    description = models.TextField(
        verbose_name="توضیحات اعلان"
    )
    
    # ارتباط با گزارش
    related_report = models.ForeignKey(
        WorkStationReport,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alerts',
        verbose_name="گزارش مرتبط"
    )
    
    # وضعیت
    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )
    
    is_acknowledged = models.BooleanField(
        default=False,
        verbose_name="تأیید شده"
    )
    
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="تأیید شده توسط"
    )
    
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="زمان تأیید"
    )
    
    # زمان‌ها
    triggered_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان فعال شدن"
    )
    
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="زمان رفع"
    )
    
    # متادیتا
    resolution_notes = models.TextField(
        blank=True,
        verbose_name="یادداشت‌های رفع"
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
        verbose_name = "اعلان ایستگاه کاری"
        verbose_name_plural = "اعلان‌های ایستگاه کاری"
        ordering = ['-triggered_at']
    
    def __str__(self):
        return f"{self.get_alert_level_display()}: {self.title}"
    
    def acknowledge(self, user):
        """تأیید اعلان"""
        self.is_acknowledged = True
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save()
    
    def resolve(self, notes=""):
        """رفع اعلان"""
        self.is_active = False
        self.resolved_at = timezone.now()
        self.resolution_notes = notes
        self.save()
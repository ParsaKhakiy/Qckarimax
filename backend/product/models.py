from django.db import models

from django.core.validators import MinValueValidator
from django.utils.text import slugify

from order.models import Order

class AbstractNameDescription(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True, allow_unicode=True)

    is_active = models.BooleanField(default=True)
    
    # زمان‌بندی
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, allow_unicode=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.title

class Product(AbstractNameDescription):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    description = models.TextField(blank=True)
    
    # قیمت و تخفیف
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    discount_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # انبارداری
    stock = models.PositiveIntegerField(default=0)


    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['id', 'slug']),
        ]

    def __str__(self):
        return self.name

    @property
    def final_price(self):
        return self.discount_price if self.discount_price else self.price



class Requirements(AbstractNameDescription):
    pass


class Operator(AbstractNameDescription):
    name = models.CharField(max_length=122)
    family = models.CharField(max_length=122)


class ProductionLine(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام خط تولید")
    location = models.CharField(max_length=100, blank=True, verbose_name="محل استقرار")
    capacity = models.PositiveIntegerField(default=5, verbose_name="ظرفیت همزمان")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "خط تولید"
        verbose_name_plural = "خطوط تولید"

    def __str__(self):
        return f"{self.name} (ظرفیت: {self.capacity})"

    @property
    def active_tasks_count(self):
        return self.production_tasks.filter(status='processing').count()

    @property
    def has_free_capacity(self):
        return self.active_tasks_count < self.capacity
    

class ProductionTask(models.Model):
    STATUS_CHOICES = (
        ('waiting', 'در انتظار'),
        ('processing', 'در حال تولید'),
        ('qc_pending', 'در انتظار QC'),
        ('qc_rejected', 'رد شده در QC'),
        ('completed', 'تکمیل شده'),
    )

    order = models.OneToOneField(
        Order, 
        on_delete=models.CASCADE, 
        related_name='production_task',
        verbose_name="سفارش"
    )
    
    production_line = models.ForeignKey(
        ProductionLine, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='production_tasks',
        verbose_name="خط تولید اختصاص یافته"
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting', verbose_name="وضعیت فعلی")
    
    timeline = models.JSONField(default=list, blank=True, verbose_name="تاریخچه تغییرات")
    
    start_date = models.DateTimeField(null=True, blank=True, verbose_name="زمان شروع")
    end_date = models.DateTimeField(null=True, blank=True, verbose_name="زمان پایان")

    class Meta:
        verbose_name = "فرآیند تولید"
        verbose_name_plural = "فرآیندهای تولید"

    def __str__(self):
        return f"تولید سفارش {self.order.id} در {self.production_line}"
    


class RequirementsProducts(AbstractNameDescription):
    product = models.OneToOneField(
        'Product',
        on_delete=models.CASCADE,
        related_name="Requirements_Products",

    )
    requirements = models.ManyToManyField(Requirements)
    product_timeline = models.ManyToManyField(
        ProductionLine
    )
    orpertors = models.ManyToManyField(Operator)

    



    
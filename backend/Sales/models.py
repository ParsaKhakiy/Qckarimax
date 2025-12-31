from django.db import models

from django.conf import settings



class SalesExpert(models.Model):
    # اتصال به یوزر سیستم
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sales_profile'
    )
    
    employee_code = models.CharField(max_length=20, unique=True, verbose_name="کد پرسنلی")
    branch = models.CharField(max_length=100, verbose_name="شعبه/واحد فروش")
    total_sales_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="مجموع فروش")

    class Meta:
        verbose_name = "کارشناس فروش"
        verbose_name_plural = "کارشناسان فروش"

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.employee_code}"
    
    
class OrderHistoryCreator(models.Model):
    saleser = models.OneToOneField(
        SalesExpert , 
        on_delete=models.DO_NOTHING  , # dont remove order from users 
        related_name='OrderHistory'
    )
    orders = models.ManyToManyField(
        'order.Order'
    )

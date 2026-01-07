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

    total_sales_product_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="مجموع فروش")
    mount_sale_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="مجموع فروش")
    product_added = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="مجموع فروش")

    customer_satisfaction = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="مجموع فروش")


    class Meta:
        verbose_name = "کارشناس فروش"
        verbose_name_plural = "کارشناسان فروش"

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.employee_code}"
    

    def add_product_amount(self):
        self.total_sales_product_amount += 1
        self.save()
    
class OrderHistoryCreator(models.Model):
    saleser = models.OneToOneField(
        SalesExpert , 
        on_delete=models.DO_NOTHING  , # dont remove order from users 
        related_name='OrderHistory'
    )
    orders = models.ManyToManyField(
        'order.Order'
    )
    def count_orders(self):
        return self.orders.count()
    
# def create_sale(user):
#     sale = SalesExpert.objects.create(
#     user = user ,
#     employee_code = token(10),
#     branch = token(10),
#     total_sales_amount = random.random(1000,100000)
#     )
#     order_history = OrderHistoryCreator.objects.create(sale = sale)
#     return sale , order_history




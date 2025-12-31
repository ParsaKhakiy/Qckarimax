from django.db import models


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('canceled', 'Canceled'),
    )

    saler = models.ForeignKey('Sales.SalesExpert', on_delete=models.CASCADE, related_name='orders')
    name = models.CharField(max_length=100)
    description = models.TextField(null=True)
    customer_name = models.CharField(max_length=100)
    customer_family = models.CharField(max_length=100)
    address = models.TextField()
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # فیلد برای کد رهگیری بانکی یا پستی
    tracking_code = models.CharField(max_length=100, blank=True, null=True)
    product = models.ForeignKey('product.Product', on_delete=models.PROTECT, related_name='order_items')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

    @property
    def full_customer_name(self):
        return f"{self.customer_name} {self.customer_family}"
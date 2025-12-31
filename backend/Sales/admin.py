from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import SalesExpert, OrderHistoryCreator

@admin.register(SalesExpert)
class SalesExpertAdmin(admin.ModelAdmin):
    # نمایش اطلاعات کلیدی در لیست
    list_display = ['get_full_name', 'employee_code', 'branch', 'total_sales_amount']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'employee_code']
    list_filter = ['branch']
    
    # متد برای نمایش نام کامل از طریق مدل User
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_full_name.short_description = "نام و نام خانوادگی"



@admin.register(OrderHistoryCreator)
class OrderHistoryCreatorAdmin(admin.ModelAdmin):
    list_display = ['saleser', 'get_orders_count']
    search_fields = ['saleser__user__username', 'saleser__employee_code']
    
    # استفاده از باکس دوطرفه برای مدیریت راحت سفارشات زیاد
    filter_horizontal = ('orders',)
    
    # جلوگیری از لود شدن کل دیتابیس در هنگام باز کردن صفحه ادمین (بهینه سازی پروداکشن)
    raw_id_fields = ['saleser']

    def get_orders_count(self, obj):
        return obj.orders.count()
    get_orders_count.short_description = "تعداد کل سفارشات ثبت شده"

    # اضافه کردن ویجت برای نمایش جزئیات سفارش‌ها در همین صفحه (اختیاری)
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('orders')
from django.contrib import admin
from .models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # ۱. ستون‌هایی که در لیست اصلی نمایش داده می‌شوند
    list_display = [
        'id', 
        'get_saler_name', 
        'full_customer_name', 
        'product', 
        'total_price', 
        'status', 
        'created_at'
    ]
    
    # ۲. فیلترهای سمت راست
    list_filter = ['status', 'city', 'created_at', 'saler__branch']
    
    # ۳. فیلدهای قابل جستجو
    search_fields = [
        'id', 
        'customer_name', 
        'customer_family', 
        'tracking_code', 
        'saler__user__username'
    ]
    
    # ۴. فیلدهای قابل ویرایش سریع در لیست
    
    
    # ۵. دسته‌بندی فیلدها در صفحه ویرایش (Fieldsets)
    fieldsets = (
        ('اطلاعات فروش', {
            'fields': ('saler', 'product', 'total_price', 'status', 'tracking_code')
        }),
        ('اطلاعات مشتری', {
            'fields': ('customer_name', 'customer_family', 'city', 'postal_code', 'address')
        }),
        ('توضیحات تکمیلی', {
            'classes': ('collapse',), # این بخش را به صورت تاشو نمایش می‌دهد
            'fields': ('name', 'description'),
        }),
    )

    # ۶. بهینه‌سازی کوئری‌ها برای جلوگیری از کندی (Select Related)
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('saler', 'product', 'saler__user')

    # متدهای کمکی برای نمایش بهتر اطلاعات
    def get_saler_name(self, obj):
        return obj.saler.user.get_full_name() or obj.saler.user.username
    get_saler_name.short_description = "کارشناس فروش"

    def full_customer_name(self, obj):
        return f"{obj.customer_name} {obj.customer_family}"
    full_customer_name.short_description = "نام مشتری"
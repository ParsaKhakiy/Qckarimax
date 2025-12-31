from django.contrib import admin

from .models import (
    Category,
    Product,
    Requirements, 
    Operator, 
    ProductionLine, 
    ProductionTask, 
    RequirementsProducts
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)} 

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'is_active', 'created_at']
    list_filter = ['is_active', 'category', 'created_at']
    list_editable = ['price', 'stock', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    list_per_page = 20



@admin.register(Requirements)
class RequirementsAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    list_display = ['name', 'family', 'id']
    search_fields = ['name', 'family']


@admin.register(RequirementsProducts)
class RequirementsProductsAdmin(admin.ModelAdmin):
    list_display = ['product', 'get_requirements_count', 'get_lines_count']
    search_fields = ['product__name']
    
    filter_horizontal = ('requirements', 'product_timeline', 'orpertors')
    
    def get_requirements_count(self, obj):
        return obj.requirements.count()
    get_requirements_count.short_description = "تعداد پیش‌نیازها"

    def get_lines_count(self, obj):
        return obj.product_timeline.count()
    get_lines_count.short_description = "تعداد خطوط عبوری"


@admin.register(ProductionLine)
class ProductionLineAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'capacity', 'active_tasks_count', 'is_full_status']
    list_filter = ['is_active']
    
    def is_full_status(self, obj):
        return obj.has_free_capacity
    is_full_status.boolean = True
    is_full_status.short_description = "ظرفیت خالی"

@admin.register(ProductionTask)
class ProductionTaskAdmin(admin.ModelAdmin):
    list_display = ['order', 'production_line', 'status', 'start_date', 'end_date']
    list_filter = ['status', 'production_line']
    search_fields = ['order__id', 'production_line__name']
    readonly_fields = ['timeline'] 
    actions = ['send_to_qc']

    @admin.action(description="ارسال موارد انتخاب شده به مرحله کنترل کیفیت")
    def send_to_qc(self, request, queryset):
        queryset.update(status='qc_pending')
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .apis import OrderViewSet, SalesExpertOrderViewSet

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'sales/orders', SalesExpertOrderViewSet, basename='sales-order')



urlpatterns = [
    path('', include(router.urls)),
    
    # APIهای اضافی
    path('orders/by-seller/', OrderViewSet.as_view({'get': 'by_seller'}), name='orders-by-seller'),
    path('orders/stats/', OrderViewSet.as_view({'get': 'orders_stats'}), name='orders-stats'),
    path('orders/recent/', OrderViewSet.as_view({'get': 'recent_orders'}), name='recent-orders'),
    
    # APIهای کارشناس فروش
    path('sales/dashboard/', SalesExpertOrderViewSet.as_view({'get': 'summary'}), name='sales-dashboard-summary'),
]
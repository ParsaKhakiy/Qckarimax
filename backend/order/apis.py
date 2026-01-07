from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta

from .models import Order
from .serializers import OrderInputSerializer, OrderOutputSerializer
from backend.utils.apis import BaseCRUDViewSet
from Sales.permissions import IsSalesExpert


class OrderViewSet(BaseCRUDViewSet):
    input_serializer_class = OrderInputSerializer
    output_serializer_class = OrderOutputSerializer
    permission_classes = [IsSalesExpert]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'city', 'product']
    search_fields = ['customer_name', 'customer_family', 'postal_code', 'tracking_code']
    ordering_fields = ['created_at', 'total_price', 'id']
    
    def get_queryset(self):
        # کاربران عادی فقط سفارش‌های خودشان را می‌بینند
        # ادمین‌ها همه سفارش‌ها را می‌بینند
        if self.request.user.is_staff:
            return Order.objects.select_related('saler', 'product').all()
        
        # اگر کاربر کارشناس فروش است
        if hasattr(self.request, 'sales_profile') and self.request.sales_profile:
            return Order.objects.filter(saler=self.request.sales_profile).select_related('saler', 'product')
        
        # اگر کاربر معمولی است (مشتری)
        if self.request.user.is_authenticated:
            return Order.objects.filter(user=self.request.user).select_related('saler', 'product')
        
        return Order.objects.none()
    
    # def get_permissions(self):
    #     if self.action in ['create', 'update', 'partial_update', 'destroy']:
    #         return [permissions.IsAuthenticated(), IsSalesExpert()]
    #     return [permissions.IsAuthenticated()]
    
    def perform_create(self, serializer):
        # ذخیره user اگر کاربر لاگین کرده
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()
    
    @action(detail=False, methods=['get'], url_path='by-seller')
    def by_seller(self, request):
        
        """سفارش‌های کارشناس فروش فعلی"""
        # if not hasattr(request, 'sales_profile') or not request.sales_profile:
        #     return Response(
        #         {'error': 'کارشناس فروش یافت نشد'},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        
        orders = Order.objects.filter(saler=request.sales_profile).select_related('product')
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='stats')
    def orders_stats(self, request):
        """آمار سفارش‌ها"""
        queryset = self.get_queryset()
        
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        stats = {
            'total_orders': queryset.count(),
            'total_revenue': queryset.aggregate(total=Sum('total_price'))['total'] or 0,
            'by_status': queryset.values('status').annotate(count=Count('id')),
            'today_orders': queryset.filter(created_at__date=today).count(),
            'week_orders': queryset.filter(created_at__date__gte=week_ago).count(),
            'month_orders': queryset.filter(created_at__date__gte=month_ago).count(),
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'], url_path='recent')
    def recent_orders(self, request):
        """سفارش‌های اخیر"""
        queryset = self.get_queryset().order_by('-created_at')[:10]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='change-status')
    def change_status(self, request, pk=None):
        """تغییر وضعیت سفارش"""
        order = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status or new_status not in dict(Order.STATUS_CHOICES):
            return Response(
                {'error': 'وضعیت معتبر نیست'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = order.status
        order.status = new_status
        order.save()
        
        return Response({
            'message': 'وضعیت سفارش با موفقیت تغییر کرد',
            'order_id': order.id,
            'new_status': new_status,
            'old_status': old_status
        })
    
    @action(detail=True, methods=['post'], url_path='update-tracking')
    def update_tracking(self, request, pk=None):
        """به‌روزرسانی کد رهگیری"""
        order = self.get_object()
        tracking_code = request.data.get('tracking_code')
        
        if not tracking_code:
            return Response(
                {'error': 'کد رهگیری الزامی است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.tracking_code = tracking_code
        order.save()
        
        return Response({
            'message': 'کد رهگیری با موفقیت بروزرسانی شد',
            'order_id': order.id,
            'tracking_code': tracking_code
        })


from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

class SalesExpertOrderViewSet(viewsets.ModelViewSet):
    """ViewSet مخصوص کارشناسان فروش"""
    serializer_class = OrderOutputSerializer
    permission_classes = [permissions.IsAuthenticated, IsSalesExpert]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return OrderInputSerializer
        return OrderOutputSerializer
    
    def get_queryset(self):
        if hasattr(self.request, 'sales_profile') and self.request.sales_profile:
            return Order.objects.filter(saler=self.request.sales_profile).select_related('product', 'saler__user')
        return Order.objects.none()
    
    def perform_create(self, serializer):
        # ثبت خودکار کارشناس فروش (حذف saler_id از داده‌های کاربر)
        validated_data = serializer.validated_data
        
        # اطمینان از وجود sales_profile
        if not hasattr(self.request, 'sales_profile') or not self.request.sales_profile:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'detail': 'کارشناس فروش یافت نشد'})
        
        # اضافه کردن کارشناس فروش فعلی
        validated_data['saler'] = self.request.sales_profile
        
        # اضافه کردن user اگر لاگین کرده
        if self.request.user.is_authenticated:
            validated_data['user'] = self.request.user
        
        serializer.save(**validated_data)
    
    def perform_update(self, serializer):
        # در به‌روزرسانی، اجازه تغییر saler را نمی‌دهیم
        if 'saler' in serializer.validated_data:
            del serializer.validated_data['saler']
        serializer.save()
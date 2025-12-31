# views/category.py
from rest_framework import filters, permissions , status
from rest_framework.decorators import action

from backend.utils.apis import BaseCRUDViewSet

from rest_framework.decorators import action
from rest_framework.response import Response


from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone


from .models import (
    Category,
    Product,
    Requirements,
    Operator,
    ProductionLine,
    ProductionTask,
    RequirementsProducts,
)


from .serializers import (
    CategoryInputSerializer,
    CategoryOutputSerializer,

    ProductInputSerializer,
    ProductOutputSerializer,

    RequirementsInputSerializer,
    RequirementsOutputSerializer,

    OperatorInputSerializer,
    OperatorOutputSerializer,
    
    ProductionLineInputSerializer,
    ProductionLineOutputSerializer,

    ProductionTaskInputSerializer,
    ProductionTaskOutputSerializer,

    RequirementsProductsInputSerializer, 
    RequirementsProductsOutputSerializer

)



class CategoryViewSet(BaseCRUDViewSet):
    input_serializer_class = CategoryInputSerializer
    output_serializer_class = CategoryOutputSerializer
    
    queryset = Category.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'slug']
    ordering_fields = ['title', 'id']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticatedOrReadOnly()]
    


# views/product.py
class ProductViewSet(BaseCRUDViewSet):
    input_serializer_class = ProductInputSerializer
    output_serializer_class = ProductOutputSerializer
    
    queryset = Product.objects.select_related('category').filter(is_active=True)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active', 'stock']
    search_fields = ['name', 'description', 'slug']
    ordering_fields = ['name', 'price', 'created_at', 'stock']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticatedOrReadOnly()]
    
    @action(detail=False, methods=['get'], url_path='out-of-stock')
    def out_of_stock(self, request):
        """محصولات ناموجود"""
        queryset = self.get_queryset().filter(stock=0)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='adjust-stock')
    def adjust_stock(self, request, pk=None):
        """تغییر موجودی محصول"""
        product = self.get_object()
        quantity = request.data.get('quantity')
        
        if not quantity or not isinstance(quantity, int):
            return Response(
                {'error': 'مقدار quantity باید یک عدد صحیح باشد'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        product.stock = max(0, product.stock + quantity)
        product.save()
        
        return Response({
            'message': f'موجودی محصول با موفقیت تغییر کرد',
            'new_stock': product.stock,
            'product_id': product.id
        })




# views/requirements.py
class RequirementsViewSet(BaseCRUDViewSet):
    input_serializer_class = RequirementsInputSerializer
    output_serializer_class = RequirementsOutputSerializer
    
    queryset = Requirements.objects.filter(is_active=True)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'slug']
    ordering_fields = ['name', 'created_at']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticatedOrReadOnly()]
    


# views/operator.py

class OperatorViewSet(BaseCRUDViewSet):
    input_serializer_class = OperatorInputSerializer
    output_serializer_class = OperatorOutputSerializer
    
    queryset = Operator.objects.filter(is_active=True)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'family', 'description', 'slug']
    ordering_fields = ['name', 'family', 'created_at']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticatedOrReadOnly()]
    

# views/production_line.py
from rest_framework import filters, permissions, status


class ProductionLineViewSet(BaseCRUDViewSet):
    input_serializer_class = ProductionLineInputSerializer
    output_serializer_class = ProductionLineOutputSerializer
    
    queryset = ProductionLine.objects.filter(is_active=True)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'location']
    ordering_fields = ['name', 'capacity', 'id']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticatedOrReadOnly()]
    
    @action(detail=False, methods=['get'], url_path='available')
    def available_lines(self, request):
        """خطوط تولید با ظرفیت آزاد"""
        lines = self.get_queryset().filter(has_free_capacity=True)
        serializer = self.get_serializer(lines, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='tasks')
    def line_tasks(self, request, pk=None):
        """نمایش وظایف یک خط تولید"""
        production_line = self.get_object()
        tasks = production_line.production_tasks.all()
        
        serializer = ProductionTaskOutputSerializer(tasks, many=True)
        
        return Response({
            'production_line': self.get_serializer(production_line).data,
            'tasks': serializer.data,
            'active_tasks_count': production_line.active_tasks_count
        })
    



# views/production_task.py

class ProductionTaskViewSet(BaseCRUDViewSet):
    input_serializer_class = ProductionTaskInputSerializer
    output_serializer_class = ProductionTaskOutputSerializer
    
    queryset = ProductionTask.objects.select_related(
        'order', 'production_line'
    ).all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'production_line']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
    
    def create(self, request, *args, **kwargs):
        """ایجاد وظیفه تولید با مدیریت خودکار تایم‌لاین"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # ایجاد تایم‌لاین اولیه
        timeline = [{
            'action': 'created',
            'timestamp': timezone.now().isoformat(),
            'user': request.user.username if request.user else 'system',
            'details': 'ایجاد وظیفه تولید'
        }]
        
        serializer.validated_data['timeline'] = timeline
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=True, methods=['post'], url_path='change-status')
    def change_status(self, request, pk=None):
        """تغییر وضعیت وظیفه تولید"""
        task = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status or new_status not in dict(task.STATUS_CHOICES):
            return Response(
                {'error': 'وضعیت معتبر نیست'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = task.status
        task.status = new_status
        
        # به‌روزرسانی تایم‌لاین
        timeline_entry = {
            'action': 'status_change',
            'timestamp': timezone.now().isoformat(),
            'user': request.user.username,
            'old_status': old_status,
            'new_status': new_status,
            'details': f'تغییر وضعیت از {old_status} به {new_status}'
        }
        
        task.timeline.append(timeline_entry)
        
        # مدیریت تاریخ‌های شروع و پایان
        if new_status == 'processing' and not task.start_date:
            task.start_date = timezone.now()
        elif new_status in ['completed', 'qc_rejected'] and not task.end_date:
            task.end_date = timezone.now()
        
        task.save()
        
        return Response({
            'message': 'وضعیت با موفقیت تغییر کرد',
            'task_id': task.id,
            'new_status': new_status,
            'old_status': old_status
        })
    
    @action(detail=False, methods=['get'], url_path='stats')
    def tasks_stats(self, request):
        """آمار وظایف تولید"""
        total = self.get_queryset().count()
        by_status = self.get_queryset().values('status').annotate(count=models.Count('id'))
        
        return Response({
            'total_tasks': total,
            'by_status': list(by_status),
            'active_lines': ProductionLine.objects.filter(is_active=True).count()
        })
    
# views/requirements_products.py


class RequirementsProductsViewSet(BaseCRUDViewSet):
    input_serializer_class = RequirementsProductsInputSerializer
    output_serializer_class = RequirementsProductsOutputSerializer
    
    queryset = RequirementsProducts.objects.select_related(
        'product'
    ).prefetch_related(
        'requirements', 'product_timeline', 'operators'
    ).filter(is_active=True)
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['product', 'is_active']
    search_fields = ['name', 'description', 'slug']
    ordering_fields = ['name', 'created_at']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]


    
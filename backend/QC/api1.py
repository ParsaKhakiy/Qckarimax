# views/production_card.py
from rest_framework import filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from datetime import timedelta

from .models import ProductionCard
from .serializers import (
    ProductionCardInputSerializer,
    ProductionCardOutputSerializer,
    ProductionCardLiteSerializer,
    ProductionCardStatusUpdateSerializer,
    ProductionCardProgressUpdateSerializer,
)
from backend.utils.apis import BaseCRUDViewSet

class ProductionCardViewSet(BaseCRUDViewSet):
    input_serializer_class = ProductionCardInputSerializer
    output_serializer_class = ProductionCardOutputSerializer
    
    queryset = ProductionCard.objects.select_related(
        'requirements_product__product__category',
        'created_by__user',
        'approved_by_qa__user',
    ).prefetch_related(
        'requirements_product__requirements',
        'requirements_product__product_timeline',
        'requirements_product__operators',
    ).filter(is_active=True)
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'status',
        'priority',
        'qc_required',
        'requirements_product',
        'created_by',
        'approved_by_qa',
    ]
    search_fields = [
        'card_code',
        'title',
        'requirements_product__product__name',
        'notes',
    ]
    ordering_fields = [
        'card_code',
        'title',
        'priority',
        'scheduled_start_date',
        'scheduled_end_date',
        'created_at',
        'current_progress',
    ]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # فیلترهای سفارشی
        is_overdue = self.request.query_params.get('is_overdue', None)
        if is_overdue is not None:
            if is_overdue.lower() == 'true':
                queryset = queryset.filter(
                    status__in=['draft', 'pending_approval', 'approved', 'in_production', 'paused'],
                    scheduled_end_date__lt=timezone.now()
                )
        
        min_progress = self.request.query_params.get('min_progress', None)
        if min_progress is not None:
            try:
                queryset = queryset.filter(current_progress__gte=int(min_progress))
            except ValueError:
                pass
        
        max_progress = self.request.query_params.get('max_progress', None)
        if max_progress is not None:
            try:
                queryset = queryset.filter(current_progress__lte=int(max_progress))
            except ValueError:
                pass
        
        # فیلتر بر اساس زمان
        start_date_from = self.request.query_params.get('start_date_from', None)
        if start_date_from:
            try:
                queryset = queryset.filter(scheduled_start_date__gte=start_date_from)
            except ValueError:
                pass
        
        start_date_to = self.request.query_params.get('start_date_to', None)
        if start_date_to:
            try:
                queryset = queryset.filter(scheduled_start_date__lte=start_date_to)
            except ValueError:
                pass
        
        return queryset
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser() | permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProductionCardLiteSerializer
        return super().get_serializer_class()
    
    def perform_create(self, serializer):
        # تنظیم کاربر ایجاد کننده
        request = self.context.get('request')
        if request and request.user:
            try:
                from .models import QualityControlExpert
                qc_expert = QualityControlExpert.objects.get(user=request.user)
                serializer.save(created_by=qc_expert)
            except QualityControlExpert.DoesNotExist:
                serializer.save()
        else:
            serializer.save()
    
    @action(detail=False, methods=['get'], url_path='stats')
    def production_stats(self, request):
        """آمار تولید"""
        total = self.get_queryset().count()
        by_status = self.get_queryset().values('status').annotate(
            count=models.Count('id')
        ).order_by('status')
        
        by_priority = self.get_queryset().values('priority').annotate(
            count=models.Count('id')
        ).order_by('priority')
        
        # کارت‌های تأخیری
        overdue_cards = self.get_queryset().filter(
            status__in=['draft', 'pending_approval', 'approved', 'in_production', 'paused'],
            scheduled_end_date__lt=timezone.now()
        ).count()
        
        # میانگین پیشرفت
        avg_progress = self.get_queryset().aggregate(
            avg_progress=models.Avg('current_progress')
        )['avg_progress'] or 0
        
        # مجموع تولید
        total_quantity = self.get_queryset().aggregate(
            total=models.Sum('quantity_to_produce')
        )['total'] or 0
        
        return Response({
            'total_cards': total,
            'overdue_cards': overdue_cards,
            'average_progress': round(avg_progress, 2),
            'total_quantity_to_produce': total_quantity,
            'cards_by_status': list(by_status),
            'cards_by_priority': list(by_priority),
        })
    
    @action(detail=False, methods=['get'], url_path='overdue')
    def overdue_cards(self, request):
        """لیست کارت‌های تأخیری"""
        overdue = self.get_queryset().filter(
            status__in=['draft', 'pending_approval', 'approved', 'in_production', 'paused'],
            scheduled_end_date__lt=timezone.now()
        )
        
        serializer = ProductionCardLiteSerializer(overdue, many=True)
        return Response({
            'count': overdue.count(),
            'cards': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='upcoming')
    def upcoming_cards(self, request):
        """کارت‌های پیش‌رو (در 7 روز آینده)"""
        next_week = timezone.now() + timedelta(days=7)
        upcoming = self.get_queryset().filter(
            scheduled_start_date__gte=timezone.now(),
            scheduled_start_date__lte=next_week,
            status__in=['draft', 'pending_approval', 'approved']
        )
        
        serializer = ProductionCardLiteSerializer(upcoming, many=True)
        return Response({
            'count': upcoming.count(),
            'cards': serializer.data
        })
    
    @action(detail=True, methods=['post'], url_path='change-status')
    def change_status(self, request, pk=None):
        """تغییر وضعیت کارت تولید"""
        card = self.get_object()
        serializer = ProductionCardStatusUpdateSerializer(
            data=request.data,
            instance=card,
            context={'request': request}
        )
        
        if serializer.is_valid():
            old_status = card.status
            new_status = serializer.validated_data['status']
            
            # تاریخ‌های شروع و پایان را بر اساس وضعیت تنظیم کن
            if new_status == 'in_production' and not card.actual_start_date:
                card.actual_start_date = timezone.now()
            elif new_status in ['completed', 'archived'] and not card.actual_end_date:
                card.actual_end_date = timezone.now()
            elif new_status == 'approved' and not card.approval_date:
                card.approval_date = timezone.now()
            
            card.status = new_status
            if 'notes' in serializer.validated_data:
                if card.notes:
                    card.notes += f"\n--- تغییر وضعیت ({timezone.now().strftime('%Y-%m-%d %H:%M')}) ---\n"
                    card.notes += f"تغییر از {old_status} به {new_status}\n"
                    card.notes += f"یادداشت: {serializer.validated_data['notes']}\n"
                else:
                    card.notes = f"تغییر وضعیت از {old_status} به {new_status}\nیادداشت: {serializer.validated_data['notes']}"
            
            card.save()
            
            return Response({
                'message': 'وضعیت با موفقیت تغییر کرد',
                'card_id': card.id,
                'old_status': old_status,
                'new_status': new_status,
                'status_display': card.get_status_display()
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='update-progress')
    def update_progress(self, request, pk=None):
        """به‌روزرسانی درصد پیشرفت"""
        card = self.get_object()
        serializer = ProductionCardProgressUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            old_progress = card.current_progress
            new_progress = serializer.validated_data['progress']
            
            card.current_progress = new_progress
            
            # اگر پیشرفت 100% شد و هنوز کامل نشده، وضعیت را تغییر بده
            if new_progress >= 100 and card.status != 'completed':
                card.status = 'completed'
                if not card.actual_end_date:
                    card.actual_end_date = timezone.now()
            
            if 'notes' in serializer.validated_data:
                if card.notes:
                    card.notes += f"\n--- به‌روزرسانی پیشرفت ({timezone.now().strftime('%Y-%m-%d %H:%M')}) ---\n"
                    card.notes += f"تغییر پیشرفت از {old_progress}% به {new_progress}%\n"
                    card.notes += f"یادداشت: {serializer.validated_data['notes']}\n"
                else:
                    card.notes = f"تغییر پیشرفت از {old_progress}% به {new_progress}%\nیادداشت: {serializer.validated_data['notes']}"
            
            card.save()
            
            return Response({
                'message': 'پیشرفت با موفقیت به‌روزرسانی شد',
                'card_id': card.id,
                'old_progress': old_progress,
                'new_progress': new_progress,
                'current_status': card.status
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], url_path='details')
    def detailed_view(self, request, pk=None):
        """نمایش جزئیات کامل کارت تولید"""
        card = self.get_object()
        serializer = ProductionCardOutputSerializer(card)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='approve')
    def approve_card(self, request, pk=None):
        """تأیید کارت تولید توسط کنترل کیفیت"""
        card = self.get_object()
        
        if card.status != 'pending_approval':
            return Response(
                {'error': 'فقط کارت‌های در انتظار تأیید قابل تأیید هستند'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # پیدا کردن کاربر کنترل کیفیت
        try:
            from .models import QualityControlExpert
            qc_expert = QualityControlExpert.objects.get(user=request.user)
        except QualityControlExpert.DoesNotExist:
            return Response(
                {'error': 'فقط کارشناسان کنترل کیفیت می‌توانند کارت‌ها را تأیید کنند'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        card.status = 'approved'
        card.approved_by_qa = qc_expert
        card.approval_date = timezone.now()
        
        if card.notes:
            card.notes += f"\n--- تأیید شده توسط کنترل کیفیت ({timezone.now().strftime('%Y-%m-%d %H:%M')}) ---\n"
            card.notes += f"تأیید کننده: {qc_expert.user.get_full_name() or qc_expert.user.username}\n"
        else:
            card.notes = f"تأیید شده توسط کنترل کیفیت در {timezone.now().strftime('%Y-%m-%d %H:%M')}\n"
            card.notes += f"تأیید کننده: {qc_expert.user.get_full_name() or qc_expert.user.username}\n"
        
        card.save()
        
        return Response({
            'message': 'کارت تولید با موفقیت تأیید شد',
            'card_id': card.id,
            'approved_by': qc_expert.user.get_full_name() or qc_expert.user.username,
            'approval_date': card.approval_date
        })
    
    @action(detail=False, methods=['get'], url_path='search-by-code')
    def search_by_code(self, request):
        """جستجوی کارت بر اساس کد"""
        card_code = request.query_params.get('code', '').strip()
        
        if not card_code:
            return Response(
                {'error': 'پارامتر code الزامی است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            card = ProductionCard.objects.get(card_code=card_code, is_active=True)
            serializer = ProductionCardOutputSerializer(card)
            return Response(serializer.data)
        except ProductionCard.DoesNotExist:
            return Response(
                {'error': 'کارت تولید با این کد یافت نشد'},
                status=status.HTTP_404_NOT_FOUND
            )
# views.py
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import * 
from .serializers import * 
from QC.permissions import IsQualityControlExpert
from django.utils import timezone 
from backend.utils.apis import BaseCRUDViewSet 




class WorkStationViewSet(BaseCRUDViewSet):
    queryset = WorkStation.objects.all()
    input_serializer_class = WorkStationInputSerializer
    output_serializer_class = WorkStationOutputSerializer
    permission_classes = [IsQualityControlExpert]
    
    @action(detail=True, methods=['get'], url_path='reports')
    def get_station_reports(self, request, pk=None):
        """گزارش‌های یک ایستگاه"""
        station = self.get_object()
        reports = station.workstation_reports.all()
        serializer = WorkStationReportOutputSerializer(reports, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='today-stats')
    def get_today_stats(self, request, pk=None):
        """آمار امروز ایستگاه"""
        station = self.get_object()
        today = timezone.now().date()
        
        stats = {
            'reports_count': station.workstation_reports.filter(
                report_date__date=today
            ).count(),
            'pending_reports': station.workstation_reports.filter(
                status='submitted'
            ).count(),
            'capacity_usage': f"{(station.today_inspections_count / station.max_daily_capacity * 100):.1f}%",
            'availability': station.availability_status
        }
        return Response(stats)

class WorkStationReportViewSet(BaseCRUDViewSet):
    queryset = WorkStationReport.objects.all()
    input_serializer_class = WorkStationReportInputSerializer
    output_serializer_class = WorkStationReportOutputSerializer
    permission_classes = [IsQualityControlExpert]
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        # فیلتر بر اساس ایستگاه کاری
        workstation = self.request.query_params.get('workstation')
        if workstation:
            qs = qs.filter(workstation_id=workstation)
        
        # فیلتر بر اساس وضعیت
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        
        # فیلتر بر اساس نوع گزارش
        report_type = self.request.query_params.get('report_type')
        if report_type:
            qs = qs.filter(report_type=report_type)
        
        return qs
    
    def perform_create(self, serializer):
        """تعیین گزارش‌دهنده هنگام ایجاد"""
        if hasattr(self.request, 'qc_profile'):
            serializer.save(reporter=self.request.qc_profile)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'], url_path='submit')
    def submit_report(self, request, pk=None):
        """ثبت گزارش"""
        report = self.get_object()
        report.status = 'submitted'
        report.save()
        return Response({'status': 'گزارش ثبت شد'})
    
    @action(detail=True, methods=['post'], url_path='approve')
    def approve_report(self, request, pk=None):
        """تأیید گزارش"""
        report = self.get_object()
        
        # بررسی سطح دسترسی
        if (not hasattr(request, 'qc_profile') or 
            request.qc_profile.qualification_level not in ['manager', 'supervisor']):
            return Response(
                {'error': 'فقط مدیر یا سرپرست می‌تواند تأیید کند'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        report.status = 'approved'
        report.approved_by = request.qc_profile
        report.approval_date = timezone.now()
        report.save()
        
        return Response({'status': 'گزارش تأیید شد'})
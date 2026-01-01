# serializers.py
from rest_framework import serializers
from .models import * 

class WorkStationInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkStation
        fields = [
            'name', 'station_type', 'location', 'department',
            'supervisor', 'qc_responsible', 'equipments', 'tools',
             'max_daily_capacity', 'working_hours',
            'status', 'is_available', 'description', 'notes'
        ]

class WorkStationOutputSerializer(serializers.ModelSerializer):
    supervisor_name = serializers.CharField(source='supervisor.get_full_name', read_only=True)
    qc_responsible_name = serializers.CharField(source='qc_responsible.user.get_full_name', read_only=True)
    station_type_display = serializers.CharField(source='get_station_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # آمار
    today_reports_count = serializers.SerializerMethodField()
    monthly_reports_count = serializers.SerializerMethodField()
    availability_status = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkStation
        fields = '__all__'
        read_only_fields = ['station_code', 'created_by', 'created_at', 'updated_at']
    
    def get_today_reports_count(self, obj):
        return obj.today_inspections_count
    
    def get_monthly_reports_count(self, obj):
        return obj.workstation_reports.filter(
            created_at__month=timezone.now().month
        ).count()
    
    def get_availability_status(self, obj):
        return obj.availability_status


class WorkStationReportInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkStationReport
        fields = [
            'workstation', 'report_type', 'title', 'priority',
            'description', 'observations', 'findings', 'measurements',
            'test_results', 'photos', 'documents', 'corrective_actions',
            'preventive_actions', 'action_deadline', 'action_responsible',
            'related_production_card', 'related_qc_inspection', 'related_order',
            'tags', 'is_urgent', 'is_confidential'
        ]
        read_only_fields = ['reporter', 'status', 'reviewed_by', 'approved_by']

class WorkStationReportOutputSerializer(serializers.ModelSerializer):
    # اطلاعات پایه
    workstation_info = serializers.SerializerMethodField()
    reporter_info = serializers.SerializerMethodField()
    report_type_display = serializers.CharField(source='get_report_type_display')
    priority_display = serializers.CharField(source='get_priority_display')
    status_display = serializers.CharField(source='get_status_display')
    
    # اطلاعات مرتبط
    production_card_info = serializers.SerializerMethodField()
    qc_inspection_info = serializers.SerializerMethodField()
    
    # زمان‌ها به فرمت خوانا
    report_date_formatted = serializers.SerializerMethodField()
    inspection_duration = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkStationReport
        fields = '__all__'
    
    def get_workstation_info(self, obj):
        return {
            'code': obj.workstation.station_code,
            'name': obj.workstation.name,
            'type': obj.workstation.get_station_type_display(),
            'location': obj.workstation.location
        }
    
    def get_reporter_info(self, obj):
        if obj.reporter:
            return {
                'name': obj.reporter.user.get_full_name(),
                'code': obj.reporter.employee_code,
                'level': obj.reporter.get_qualification_level_display()
            }
        return None
    
    def get_production_card_info(self, obj):
        if obj.related_production_card:
            return {
                'card_code': obj.related_production_card.card_code,
                'title': obj.related_production_card.title
            }
        return None
    
    def get_qc_inspection_info(self, obj):
        if obj.related_qc_inspection:
            return {
                'inspection_code': obj.related_qc_inspection.inspection_code,
                'type': obj.related_qc_inspection.get_inspection_type_display()
            }
        return None
    
    def get_report_date_formatted(self, obj):
        return obj.report_date.strftime('%Y/%m/%d %H:%M') if obj.report_date else None
    
    def get_inspection_duration(self, obj):
        return obj.calculate_inspection_duration()
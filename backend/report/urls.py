# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkStationViewSet , WorkStationReportViewSet

router = DefaultRouter()
router.register(r'workstations', WorkStationViewSet, basename='workstation')
router.register(r'workstation-reports', WorkStationReportViewSet, basename='workstation-report')

urlpatterns = [
    path('', include(router.urls)),
]

# ====== URLهای تولید شده ======
"""
WorkStation URLs:
GET     /api/workstations/                     # لیست ایستگاه‌ها
POST    /api/workstations/                     # ایجاد ایستگاه
GET     /api/workstations/{id}/                # جزئیات ایستگاه
PUT     /api/workstations/{id}/                # به‌روزرسانی کامل
PATCH   /api/workstations/{id}/                # به‌روزرسانی جزئی
DELETE  /api/workstations/{id}/                # حذف ایستگاه
GET     /api/workstations/{id}/reports/        # گزارش‌های ایستگاه
GET     /api/workstations/{id}/today-stats/    # آمار امروز ایستگاه

WorkStationReport URLs:
GET     /api/workstation-reports/              # لیست گزارش‌ها
POST    /api/workstation-reports/              # ایجاد گزارش
GET     /api/workstation-reports/{id}/         # جزئیات گزارش
PUT     /api/workstation-reports/{id}/         # به‌روزرسانی کامل
PATCH   /api/workstation-reports/{id}/         # به‌روزرسانی جزئی
DELETE  /api/workstation-reports/{id}/         # حذف گزارش
POST    /api/workstation-reports/{id}/submit/  # ثبت گزارش
POST    /api/workstation-reports/{id}/approve/ # تأیید گزارش
"""
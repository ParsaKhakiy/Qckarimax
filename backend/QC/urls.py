from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api1 import (

    ProductionCardViewSet,  # اضافه کردن این خط
)
from .api2 import (
QualityControlExpertViewSet,
ProductionCardQCInspectionViewSet,
)

router = DefaultRouter()
router.register(r'production-cards', ProductionCardViewSet, basename='production-card')  # اضافه کردن این خط
router.register(r'qc-experts', QualityControlExpertViewSet, basename='qc-expert')
router.register(r'qc-inspections', ProductionCardQCInspectionViewSet, basename='qc-inspection')
urlpatterns = [
    path('', include(router.urls)),
]



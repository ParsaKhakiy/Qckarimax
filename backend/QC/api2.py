# views.py
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from backend.utils.apis import BaseCRUDViewSet

from .permissions import (
    IsQualityControlExpert,
)
from .serializers2 import *



class QualityControlExpertViewSet(BaseCRUDViewSet):
    """
    ViewSet برای مدیریت کارشناسان کنترل کیفیت
    """

    queryset = QualityControlExpert.objects.filter(is_active=True).select_related(
        "user"
    )
    input_serializer_class = QualityControlExpertInputSerializer
    output_serializer_class = QualityControlExpertOutputSerializer

    # def get_permissions(self):
    #     if self.action in ['create', 'update', 'partial_update', 'destroy']:
    #         permission_classes = [CanManageQCStaff]  # فقط مدیران
    #     else:
    #         permission_classes = [IsQualityControlExpert]  # همه کارشناسان QC
    #     return [permission() for permission in permission_classes]

    def get_queryset(self):
        """فیلتر کردن queryset بر اساس سطح دسترسی"""
        qs = super().get_queryset()

        # اگر کاربر مدیر QC نیست، فقط اطلاعات خودش را ببیند
        request = self.request
        if hasattr(
            request, "qc_profile"
        ) and request.qc_profile.qualification_level not in ["manager", "supervisor"]:
            qs = qs.filter(user=request.user)

        return qs

    @action(detail=False, methods=["get"], url_path="stats")
    def get_statistics(self, request):
        """
        آمار کارشناسان QC
        GET /api/qc-experts/stats/
        """
        total_experts = self.get_queryset().count()

        stats = {
            "total_experts": total_experts,
            "by_level": {
                "basic": self.get_queryset()
                .filter(qualification_level="basic")
                .count(),
                "senior": self.get_queryset()
                .filter(qualification_level="senior")
                .count(),
                "supervisor": self.get_queryset()
                .filter(qualification_level="supervisor")
                .count(),
                "manager": self.get_queryset()
                .filter(qualification_level="manager")
                .count(),
            },
            "active_count": self.get_queryset().filter(is_active=True).count(),
            "average_approval_rate": self.get_queryset().aggregate(
                avg=models.Avg("approval_rate")
            )["avg"]
            or 0,
        }

        return Response(stats)

    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate_expert(self, request, pk=None):
        """
        غیرفعال کردن کارشناس QC
        POST /api/qc-experts/{id}/deactivate/
        """
        expert = self.get_object()

        # فقط مدیران می‌توانند غیرفعال کنند
        if (
            not hasattr(request, "qc_profile")
            or request.qc_profile.qualification_level != "manager"
        ):
            return Response(
                {"error": "فقط مدیر QC می‌تواند کارشناسان را غیرفعال کند"},
                status=status.HTTP_403_FORBIDDEN,
            )

        expert.is_active = False
        expert.save()

        return Response({"status": "کارشناس غیرفعال شد"})


def getQCInspectionByCardId(production_card_id):  # TODO use related name
    return ProductionCardQCInspection.objects.filter(
        production_card_id=production_card_id
    )


class ProductionCardQCInspectionViewSet(BaseCRUDViewSet):
    """
    ViewSet برای مدیریت بازرسی‌های QC کارت تولید
    """
    permission_classes = [IsQualityControlExpert]
    queryset = ProductionCardQCInspection.objects.all().select_related(
        "production_card", "inspector", "approved_by_qc_manager"
    )
    input_serializer_class = ProductionCardQCInspectionInputSerializer
    output_serializer_class = ProductionCardQCInspectionOutputSerializer

    def get_queryset(self):
        """فیلتر کردن queryset بر اساس کاربر"""
        qs = super().get_queryset()
        request = self.request

        if hasattr(request, "qc_profile"):
            qc_profile = request.qc_profile

            # اگر کاربر مدیر یا سرپرست نیست، فقط بازرسی‌های خودش را ببیند
            if qc_profile.qualification_level not in ["manager", "supervisor"]:
                qs = qs.filter(inspector=qc_profile)

            # فیلتر بر اساس وضعیت
            status_filter = request.query_params.get("status")
            if status_filter:
                qs = qs.filter(status=status_filter)

            # فیلتر بر اساس نوع بازرسی
            inspection_type = request.query_params.get("inspection_type")
            if inspection_type:
                qs = qs.filter(inspection_type=inspection_type)

        return qs

    def get_serializer_context(self):
        """اضافه کردن context به serializer"""
        context = super().get_serializer_context()
        context["request"] = self.request

        if hasattr(self.request, "qc_profile"):
            context["qc_profile"] = self.request.qc_profile

        return context


    
    
    # Here Get the each by cart 
    @action(methods=["GET"], detail=True, url_path="cart-inspections/prod_cart=<int:pk>")
    def get_cart_inspections(self, pk=None, *args, **kwargs):
        try:
            result = getQCInspectionByCardId(pk)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            ProductionCardOutputSerializer(result, many=True).data
        )


    
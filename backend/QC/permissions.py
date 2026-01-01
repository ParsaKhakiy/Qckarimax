
from rest_framework.permissions import BasePermission
from .models import QualityControlExpert

class IsQualityControlExpert(BasePermission):
    """
    بررسی می‌کند که کاربر وارد شده یک کارشناس کنترل کیفیت باشد
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            qc_profile = QualityControlExpert.objects.select_related('user').get(
                user=request.user,
                is_active=True  # فقط کارشناسان فعال
            )
            
            # TODO  check QC controll 
            request.qc_profile = qc_profile
            return True
            
        except QualityControlExpert.DoesNotExist:
            return False
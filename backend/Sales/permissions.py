from rest_framework.permissions import IsAuthenticated , BasePermission
from .models import SalesExpert

class IsSalesExpert(BasePermission):
    "The requests user must be SalesExpert Instance"

    def has_permission(self, request, view):
        # TODO add middle ware for this section
        if not request.user or not request.user.is_authenticated:
            return False
        try:
            sales_profile = SalesExpert.objects.select_related('user').get(user=request.user)
            
            request.sales_profile = sales_profile
            return True
            
        except SalesExpert.DoesNotExist:
            return False
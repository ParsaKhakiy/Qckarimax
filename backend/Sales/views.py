from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from .permissions  import IsSalesExpert



class SaleTokenRefreshView(TokenRefreshView):
    permission_classes =  IsSalesExpert


class saleTokenVerifyView(TokenVerifyView):
    permission_classes =  IsSalesExpert

# session set
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView


from .serializers import TokenObtainClassc




class TokenObtainPairViewC(TokenObtainPairView):
    serializer_class = TokenObtainClassc
# set session when we send jwt 
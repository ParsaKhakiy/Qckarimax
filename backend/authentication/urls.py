from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from .apis import TokenObtainPairViewC


urlpatterns = [
        path('jwt/', include(([
            path('login/', TokenObtainPairViewC.as_view(),name="login"),
            path('refresh/', TokenRefreshView.as_view(),name="refresh"),
            path('verify/', TokenVerifyView.as_view(),name="verify"),
            ], "jwt")),),
]



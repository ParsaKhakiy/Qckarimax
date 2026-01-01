"""
URL configuration for backend project.
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
   openapi.Info(
      title="esfhan mohadam API",
      default_version='v1',
      description="Enterprise Esfhan Mohadam API",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="parsakhakiy@gmail.com"),
      license=openapi.License(name="BSD License <Esfhan Mogadam>"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('payment.api.urls')),
    path('product/' ,include('product.urls') ),
    path('QC/' ,include('QC.urls') ),
    path('repost/' ,include('report.urls') ),

    path('salles-api/',include('Sales.urls')),
    
    # Swagger/OpenAPI documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),

]

# Source - https://stackoverflow.com/q
# Posted by CodeMantle
# Retrieved 2025-11-26, License - CC BY-SA 4.0

if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns += [path(r'^__debug__/', include(debug_toolbar.urls))]
    except ImportError:
        pass

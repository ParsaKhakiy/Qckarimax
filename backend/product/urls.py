# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .apis import (
    CategoryViewSet,
    ProductViewSet,
    RequirementsViewSet,
    OperatorViewSet,
    ProductionLineViewSet,
    ProductionTaskViewSet,
    RequirementsProductsViewSet,
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'requirements', RequirementsViewSet, basename='requirement')
router.register(r'operators', OperatorViewSet, basename='operator')
router.register(r'production-lines', ProductionLineViewSet, basename='production-line')
router.register(r'production-tasks', ProductionTaskViewSet, basename='production-task')
router.register(r'requirements-products', RequirementsProductsViewSet, basename='requirements-products')

urlpatterns = [
    path('product/', include(router.urls)),
]
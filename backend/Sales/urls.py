from django.urls import path

from .api import OrderBySallerApiView

urlpatterns = [
    path("add-orders/", OrderBySallerApiView.as_view(), name="orders"),
]

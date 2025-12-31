from django.urls import path

from .api import OrderBySellerApiView

urlpatterns = [
    path("add-orders/", OrderBySellerApiView.as_view(), name="orders"),
]

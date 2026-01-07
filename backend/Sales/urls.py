from django.urls import path

from .api import OrderBySellerApiView , DashbordApiView
from django.urls import path, include


urlpatterns = [
    path("add-orders/", OrderBySellerApiView.as_view(), name="orders"),
    path("dashbord/" , DashbordApiView.as_view() , name='Dashbord'),
    
]





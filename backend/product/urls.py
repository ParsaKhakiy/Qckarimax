from django.urls import path 
from .views import TestProduct
from rest_framework.routers import DefaultRouter

route  = DefaultRouter()
route.register('testproduct' , TestProduct , 'test_prooeduct')

urlpatterns = route.urls

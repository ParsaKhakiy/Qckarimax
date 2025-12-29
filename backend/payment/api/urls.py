"""
URL routing for Payment API
"""
from django.urls import path
from . import views

app_name = 'payment_api'

urlpatterns = [
    path('payments/initialize/', views.initialize_payment, name='initialize-payment'),
    path('payments/verify/', views.verify_payment, name='verify-payment'),
    path('payments/<uuid:payment_id>/status/', views.get_payment_status, name='payment-status'),
]


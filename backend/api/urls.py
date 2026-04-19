"""
URL configuration for API app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('test/', views.test_json, name='test_json'),
    path('simulate/run/', views.run_simulation, name='run_simulation'),
]

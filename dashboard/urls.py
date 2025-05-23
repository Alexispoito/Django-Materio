from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('top-customers/', views.top_customers_list, name='top_customers_list'),
]

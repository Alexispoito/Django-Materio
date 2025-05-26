from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('top-customers/', views.top_customers_list, name='top_customers_list'),
    path('top-products-bar-data/', views.top_products_bar_data, name='top_products_bar_data'),
    path('api/monthly-profit/', views.monthly_profit_data, name='monthly_profit_data'),
]

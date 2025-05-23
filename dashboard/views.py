from django.shortcuts import render
from .models import Customers, Orders, Products, Employees, OrderDetails
from django.db.models import Sum, Count

def dashboard(request):
    context = {
        # Order and Customer Metrics
        'metrics': {
            'total_customers': Customers.objects.count(),
            'total_orders': Orders.objects.count(),
            'total_products': Products.objects.count(),
            'employee_count': Employees.objects.count(),
        },

        # Top Products (by quantity sold)
        'top_products': Products.objects.annotate(
            quantity_sold=Sum('orderdetails__quantity')
        ).order_by('-quantity_sold')[:10],

        # Top Customers (by order count)
        'top_customers': Customers.objects.annotate(
            order_count=Count('orders')
        ).order_by('-order_count')[:10],

        'top_2_customers': Customers.objects.annotate(
            order_count=Count('orders')
        ).order_by('-order_count')[:2],

        # Employee performance (orders handled)
        'employee_orders': Employees.objects.annotate(
            handled_orders=Count('orders')
        ).order_by('-handled_orders')[:5],

        'recent_orders': Orders.objects.select_related('customer', 'employee').order_by('-order_date')[:10],
        # Colors for chart/avatars (optional)
        'colors': ['primary', 'success', 'warning', 'danger', 'info']
    }

    return render(request, 'dashboard/index.html', context)

def top_customers_list(request):
    top_customers = Customers.objects.annotate(
        order_count=Count('orders')
    ).order_by('-order_count')

    return render(request, 'dashboard/top_customers_list.html', {
        'top_customers': top_customers
    })

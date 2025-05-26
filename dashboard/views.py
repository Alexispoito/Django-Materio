from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Sum, Count, F, DecimalField
from django.db.models.functions import ExtractMonth
from datetime import datetime
from decimal import Decimal
from django.templatetags.static import static  # <-- For static file URLs
from django.db.models.functions import TruncMonth

from .models import Customers, Orders, Products, Employees, OrderDetails

def dashboard(request):
    # Total earnings and growth calculation
    total_earnings = OrderDetails.objects.aggregate(
        total=Sum(F('quantity') * F('unit_price'), output_field=DecimalField())
    )['total'] or Decimal('0.00')

    last_year_earnings = total_earnings * Decimal('0.9')  # 10% assumed growth
    growth_percent = 10

    # Top earning products with images
    top_earning_products = Products.objects.order_by('-list_price')[:3]

    weekly_profit = total_earnings * Decimal('0.3')  # Example value (30% of total)

    # Yearly sales for 2006
    sales_2006 = OrderDetails.objects.filter(
        order__order_date__year=2006
    ).aggregate(
        total=Sum(F('quantity') * F('unit_price'), output_field=DecimalField())
    )['total'] or Decimal('0.00')

    product_icons = [
        static('img/products/marmalade.png'),
        static('img/products/dried_apples.png'),
        static('img/products/coffee.png'),
    ]

    top_clients = []
    for i, product in enumerate(top_earning_products):
        top_clients.append({
            'name': product.product_name or 'N/A',
            'stack': product.category or 'Unknown',
            'total_sales': float(product.list_price),
            'percent': 75 - (i * 10),  # just example logic
            'icon_url': product_icons[i] if i < len(product_icons) else static('assets/img/products/default.png'),
        })

    context = {
        'metrics': {
            'total_customers': Customers.objects.count(),
            'total_orders': Orders.objects.count(),
            'total_products': Products.objects.count(),
            'employee_count': Employees.objects.count(),
        },
        'weekly_profit': weekly_profit,
        'total_earnings': total_earnings,
        'sales_2006': sales_2006,
        'last_year_earnings': last_year_earnings,
        'growth_percent': growth_percent,
        'top_clients': top_clients,
        'top_products': Products.objects.annotate(
            quantity_sold=Sum('orderdetails__quantity')
        ).order_by('-quantity_sold')[:10],
        'top_customers': Customers.objects.annotate(
            order_count=Count('orders')
        ).order_by('-order_count')[:10],
        'top_2_customers': Customers.objects.annotate(
            order_count=Count('orders')
        ).order_by('-order_count')[:2],
        'employee_orders': Employees.objects.annotate(
            handled_orders=Count('orders')
        ).order_by('-handled_orders')[:5],
        'recent_orders': Orders.objects.select_related('customer', 'employee').order_by('-order_date')[:10],
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

def top_products_bar_data(request):
    # Get top 5 products by quantity sold
    top_products = Products.objects.annotate(
        quantity_sold=Sum('orderdetails__quantity')
    ).order_by('-quantity_sold')[:5]

    # Prepare data for chart
    labels = [product.product_name for product in top_products]
    data = [product.quantity_sold or 0 for product in top_products]

    return JsonResponse({
        'labels': labels,
        'data': data,
    })

def monthly_profit_data(request):
    data = (
        OrderDetails.objects
        .annotate(month=TruncMonth('order__order_date'))
        .values('month')
        .annotate(total=Sum(F('quantity') * F('unit_price'), output_field=DecimalField()))
        .order_by('month')
    )

    labels = [d['month'].strftime('%b %Y') for d in data]
    profits = [float(d['total']) for d in data]

    return JsonResponse({
        'labels': labels,
        'data': profits,
    })

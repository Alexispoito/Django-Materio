from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Sum, Count, F, DecimalField
from django.db.models.functions import ExtractMonth
from datetime import datetime
from decimal import Decimal
from django.templatetags.static import static
from django.db.models.functions import TruncMonth

from .models import Customers, Orders, Products, Employees, OrderDetails

def dashboard(request):
    total_earnings = OrderDetails.objects.aggregate(
        total=Sum(F('quantity') * F('unit_price'), output_field=DecimalField())
    )['total'] or Decimal('0.00')

    last_year_earnings = total_earnings * Decimal('0.9')  # 10% assumed growth
    growth_percent = 10

    top_earning_products = Products.objects.order_by('-list_price')[:3]
    weekly_profit = total_earnings * Decimal('0.3')

    sales_2006 = OrderDetails.objects.filter(
        order__order_date__year=2006
    ).aggregate(
        total=Sum(F('quantity') * F('unit_price'), output_field=DecimalField())
    )['total'] or Decimal('0.00')

    city_sales = (
    OrderDetails.objects
    .select_related('order')
    .values('order__ship_city')  # ← Group by shipping city
    .annotate(total_sales=Sum(F('quantity') * F('unit_price')))
    .order_by('-total_sales')[:5]
    )

    sales_by_cities = []
    for i, entry in enumerate(city_sales):
        city_name = entry['order__ship_city'] or 'Unknown'
        sales_by_cities.append({
            'city': city_name,
            'code': city_name[:2].upper(),
            'total_sales': round(entry['total_sales'] or Decimal(0), 2),
            'sales_count': int(entry['total_sales'] or 0) // 10_000,
            'trend': 'up' if i % 2 == 0 else 'down',
            'percent': [25.8, 6.2, 12.4, 11.9, 16.2][i] if i < 5 else 10.0
        })

    top_city_sales = Orders.objects.values('ship_city') \
    .annotate(total_quantity=Sum('orderdetails__quantity')) \
    .order_by('-total_quantity')[:5]


    # Format for context
    top_city_sales = [
        {'name': item['ship_city'], 'total_quantity': item['total_quantity']}
        for item in top_city_sales
    ]


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
            'percent': 75 - (i * 10),
            'icon_url': product_icons[i] if i < len(product_icons) else static('assets/img/products/default.png'),
        })

    # Group by payment_type and count usage
    payment_types = Orders.objects.values('payment_type').annotate(count=Count('id')).order_by('-count')

    # Rename the key to `name` for easier use in template
    for pt in payment_types:
        pt['name'] = pt.pop('payment_type')

    context = {
        'metrics': {
            'total_customers': Customers.objects.count(),
            'total_orders': Orders.objects.count(),
            'total_products': Products.objects.count(),
            'employee_count': Employees.objects.count(),
        },
        'payment_types': payment_types,
        'top_city_sales': top_city_sales,
        'sales_by_countries': sales_by_cities,
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
        ).order_by('-handled_orders')[:7],
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

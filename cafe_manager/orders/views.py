from django.shortcuts import render
from orders.services import OrderService
from orders.models import OrderStatus


def order_list(request):
    filter_by = request.GET.get("filter_by", "table_number")

    if filter_by == "table_number":
        table_number = request.GET.get("table_number")
        orders = OrderService.search_by_filters(
            table_number=table_number, normalized=True
        )
    elif filter_by == "status":
        status = request.GET.get("status")
        orders = OrderService.search_by_filters(
            status=str(status), normalized=True
        )
    else:
        orders = OrderService.search_by_filters()

    return render(
        request,
        "order_list.html",
        {
            "orders": orders,
            "filter_by": filter_by,
            "statuses": [choice[1] for choice in OrderStatus.choices],
        },
    )

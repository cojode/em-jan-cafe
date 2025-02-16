from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import ValidationError
from orders.models import Dish, OrderStatus, Order
from orders.services import OrderService


def order_list(request):
    supported_order_search_filters = ["table_number", "status"]

    order_filters = {
        filter: request.GET.get(filter)
        for filter in supported_order_search_filters
    }

    orders = OrderService.search_by_filters(normalized=True, **order_filters)

    return render(
        request,
        "order_list.html",
        {
            "orders": orders,
            "statuses": list(OrderStatus.choices),
        },
    )


def _process_dishes_from_request(request):
    """
    Helper function to extract and validate dishes and quantities from the request.
    """
    dish_ids = request.POST.getlist("dishes")
    quantities = request.POST.getlist("quantities")
    dishes = []
    for dish_id, quantity in zip(dish_ids, quantities):
        if quantity.isdigit() and int(quantity) > 0:
            dishes.append({"dish_id": int(dish_id), "quantity": int(quantity)})
    if not dishes:
        raise ValidationError(
            "Выберите хотя бы одно блюдо с количеством больше 0"
        )
    return dishes


def order_create(request):
    template_name = "order_create.html"
    if request.method == "POST":
        try:
            table_number = request.POST.get("table_number")
            dishes = _process_dishes_from_request(request)
            OrderService.create(table_number, dishes)
            return redirect("order_list")
        except ValidationError as e:
            return render(
                request,
                template_name,
                {
                    "dishes": Dish.objects.all(),
                    "error": str(e.message),
                },
            )

    dishes = Dish.objects.all()
    return render(request, template_name, {"dishes": dishes})


def order_edit(request, order_id):
    template_name = "order_edit.html"
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        try:
            dishes = _process_dishes_from_request(request)
            OrderService.modify_dishes_by_id(order_id, dishes)
            return redirect("order_list")
        except ValidationError as e:
            return render(
                request,
                template_name,
                {
                    "order": order,
                    "dishes": Dish.objects.all(),
                    "error": str(e.message),
                },
            )

    dishes = Dish.objects.all()
    return render(
        request,
        template_name,
        {
            "order": order,
            "dishes": dishes,
        },
    )


def order_delete(_, order_id):
    OrderService.remove_by_id(order_id)
    return redirect("order_list")

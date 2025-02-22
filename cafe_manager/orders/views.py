from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse

from orders.models import OrderStatus
from orders.services import (DishService, OrderService, OrderServiceError,
                             SearchError)


def order_list(request):
    """
    Displays a list of orders filtered by optional query parameters.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered order list page with filtered orders and status choices.
    """
    filters = {
        filter: request.GET.get(filter)
        for filter in ["table_number", "status", "order_id"]
        if request.GET.get(filter)
    }
    # ? order_id <=> Order PK <=> "pk"
    filters["pk"] = filters.pop("order_id", None)
    orders = OrderService.search_by_filters(
        apply_prefetch=True, normalized=True, **filters
    )
    return render(
        request,
        "order_list.html",
        {"orders": orders, "statuses": OrderStatus.choices},
    )


def _process_dishes(request):
    """
    Processes dish data from the request to create a list of dishes with quantities.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        list: A list of dictionaries containing dish IDs and quantities.

    Raises:
        ValidationError: If no valid dishes with quantities are provided.
    """
    dish_ids = request.POST.getlist("dishes")
    quantities = request.POST.getlist("quantities")
    dishes = [
        {"dish_id": int(dish_id), "quantity": int(qty)}
        for dish_id, qty in zip(dish_ids, quantities)
        if qty.isdigit() and int(qty) > 0
    ]
    if not dishes:
        raise ValidationError("Выберите хотя бы одно блюдо с количеством больше 0")
    return dishes


def order_create(request):
    """
    Handles the creation of a new order.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered order creation page or redirects to the order list page.
    """
    if request.method == "POST":
        try:
            dishes = _process_dishes(request)
            OrderService.create(request.POST.get("table_number"), dishes)
            return redirect("order_list")
        except ValidationError as e:
            return render(
                request,
                "order_create.html",
                {"dishes": DishService.all_dishes(), "error": str(e)},
            )
    return render(request, "order_create.html", {"dishes": DishService.all_dishes()})


def order_edit(request, order_id):
    """
    Handles the editing of an existing order.

    Args:
        request (HttpRequest): The HTTP request object.
        order_id (int): The ID of the order to be edited.

    Returns:
        HttpResponse: Rendered order edit page or redirects to the order list page.

    Raises:
        Http404: If the order with the specified ID is not found.
    """
    try:
        order = OrderService.search_by_id(order_id, apply_prefetch=True)
    except SearchError:
        raise Http404("Order not found") from SearchError

    if request.method == "POST":
        try:
            dishes = _process_dishes(request)
            OrderService.modify_dishes_by_id(order_id, dishes)
            return redirect("order_list")
        except ValidationError as e:
            return render(
                request,
                "order_edit.html",
                {
                    "order": order,
                    "dishes": DishService.all_dishes(),
                    "error": str(e),
                },
            )
    return render(
        request,
        "order_edit.html",
        {"order": order, "dishes": DishService.all_dishes()},
    )


def _order_list_with_query_params(request):
    """
    Constructs a URL for the order list page with preserved query parameters.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        str: The URL for the order list page with query parameters.
    """
    query_params = request.GET.urlencode()
    redirect_url = reverse("order_list")
    if query_params:
        redirect_url += f"?{query_params}"
    return redirect_url


def order_delete(request, order_id):
    """
    Handles the deletion of an order.

    Args:
        request (HttpRequest): The HTTP request object.
        order_id (int): The ID of the order to be deleted.

    Returns:
        HttpResponse: Redirects to the order list page with a success or error message.
    """
    try:
        OrderService.remove_by_id(order_id)
        messages.success(request, "Заказ успешно удален!")
    except OrderServiceError as e:
        messages.error(request, f"Ошибка при удалении заказа: {str(e)}")
    return redirect(_order_list_with_query_params(request))


def update_order_status(request, order_id):
    """
    Handles the updating of an order's status.

    Args:
        request (HttpRequest): The HTTP request object.
        order_id (int): The ID of the order to be updated.

    Returns:
        HttpResponse: Redirects to the order list page with a success or error message.
    """
    if request.method == "POST":
        try:
            new_status = request.POST.get("status")
            OrderService.modify_status_by_id(order_id, new_status)
            messages.success(request, "Статус успешно обновлен!")
        except OrderServiceError as e:
            messages.error(request, f"Ошибка при обновлении статуса: {str(e)}")

    return redirect(_order_list_with_query_params(request))


def profit_view(request):
    """
    Displays the total profit from all orders.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered profit page with the total profit.
    """
    total_profit = OrderService.calculate_profit()
    return render(request, "profit.html", {"total_profit": total_profit})

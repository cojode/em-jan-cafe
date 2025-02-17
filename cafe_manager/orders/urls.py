from django.urls import include, path

from orders.views import (order_create, order_delete, order_edit, order_list,
                          profit_view, update_order_status)

urlpatterns = [
    path("api/", include("orders.api.urls")),
    path("orders/", order_list, name="order_list"),
    path("orders/create/", order_create, name="order_create"),
    path(
        "orders/<int:order_id>/edit/",
        order_edit,
        name="order_edit",
    ),
    path(
        "orders/<int:order_id>/update_status/",
        update_order_status,
        name="update_order_status",
    ),
    path("orders/<int:order_id>/delete/", order_delete, name="order_delete"),
    path("orders/profit/", profit_view, name="profit_view"),
]

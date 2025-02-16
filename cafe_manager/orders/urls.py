from django.urls import include, path
from orders.views import (
    order_list,
    order_create,
    order_edit,
    order_delete,
)

urlpatterns = [
    path("api/", include("orders.api.urls")),
    path("orders/", order_list, name="order_list"),
    path("orders/create/", order_create, name="order_create"),
    path(
        "orders/<int:order_id>/edit/",
        order_edit,
        name="order_edit",
    ),
    path("orders/<int:order_id>/delete/", order_delete, name="order_delete"),
]

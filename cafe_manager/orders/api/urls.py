from django.urls import path
from . import views

urlpatterns = [
    path("orders/", views.OrderView.as_view(), name="order-list"),
    path(
        "orders/<int:order_id>",
        views.OrderIdView.as_view(),
        name="order-detail",
    ),
    path(
        "orders/<int:order_id>/status",
        views.OrderIdStatusView.as_view(),
        name="order-status",
    ),
    path(
        "orders/<int:order_id>/items",
        views.OrderIdItemsView.as_view(),
        name="order-items",
    ),
    path("orders/revenue", views.RevenueView.as_view(), name="order-revenue"),
]

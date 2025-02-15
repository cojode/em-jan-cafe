from django.urls import path
from . import views

urlpatterns = [
    path("orders/", views.OrderView.as_view()),
    path(
        "orders/<int:order_id>",
        views.OrderIdView.as_view(),
    ),
    path(
        "orders/<int:order_id>/status",
        views.OrderIdStatusView.as_view(),
    ),
    path(
        "orders/revenue",
        views.RevenueView.as_view(),
    ),
]

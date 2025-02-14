from django.urls import path
from . import views

urlpatterns = [
    path(
        "create",
        views.OrderCreateView.as_view(),
        name="create order",
    ),
    path("all", views.OrderListView.as_view(), name="list orders"),
    path("<int:order_id>", views.OrderIdView.as_view(), name="order by id"),
    path(
        "table/<int:table_number>",
        views.OrderTableNumberView.as_view(),
        name="orders by table number",
    ),
    path(
        "<int:order_id>/status",
        views.OrderIdStatusView.as_view(),
        name="order status access by id",
    ),
    path(
        "total-profit",
        views.TotalProfitView.as_view(),
        name="calculated total profit",
    ),
]

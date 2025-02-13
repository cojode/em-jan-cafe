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
]

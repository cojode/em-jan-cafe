from django.urls import include, path
from orders import views

urlpatterns = [
    path("api/", include("orders.api.urls")),
    path("orders/", views.order_list),
]

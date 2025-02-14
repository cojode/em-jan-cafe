from django.urls import path, include

urlpatterns = [
    path("api/orders/", include("orders.api.urls")),
    # path("", include("orders.web.interface.urls")),
]

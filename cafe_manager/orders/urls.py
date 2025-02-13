from django.urls import path, include

urlpatterns = [
    path("api/", include("orders.web.api.urls")),
    path("", include("orders.web.interface.urls")),
]

from django.urls import path
from . import views

urlpatterns = [
    path(
        "create-order",
        views.OrderCreateView.as_view(),
        name="create-order",
    ),
]

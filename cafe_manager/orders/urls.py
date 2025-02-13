from . import web
from django.urls import path


urlpatterns = [
    path("api/home", web.api.home, name="api"),
    path("home", web.views.home, name="views"),
]

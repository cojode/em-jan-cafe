from django.shortcuts import HttpResponse


def ping(_):
    return HttpResponse("pong")

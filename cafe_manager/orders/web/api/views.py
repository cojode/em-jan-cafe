from django.shortcuts import HttpResponse

# ! not DRF for sure


def ping(_):
    return HttpResponse("pong")

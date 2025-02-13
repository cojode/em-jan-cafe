from django.shortcuts import HttpResponse


def home(_):
    return HttpResponse("Hello from api")

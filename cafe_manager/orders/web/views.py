from django.shortcuts import HttpResponse


def home(_):
    return HttpResponse("Hello form views")

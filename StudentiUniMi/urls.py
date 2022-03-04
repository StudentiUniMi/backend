"""StudentiUniMi URL Configuration

The `urlpatterns` list routes URLs to views.
"""
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponse, HttpRequest
from django.urls import path, include
from django.views.generic import RedirectView
from sentry_sdk import configure_scope

import telegrambot.urls
import university.urls

admin.site.site_header = "Network StudentiUniMi - administration"


def healthcheck(_: HttpRequest) -> HttpResponse:
    with configure_scope() as scope:
        if scope.transaction:
            scope.transaction.sampled = False
    return HttpResponse("hello, you hacker!\n", content_type="text/plain")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(university.urls)),
    path('telegrambot/', include(telegrambot.urls)),
    url(r'^robots.txt$', lambda r: HttpResponse(
        "User-Agent: *\nDisallow: /",
        content_type="text/plain",
    ), name="robots_txt"),
    url(r"^healthcheck$", healthcheck, name="healthcheck"),
]

if not settings.DEBUG:
    urlpatterns.append(
        path('', RedirectView.as_view(url="https://api.studentiunimi.it/admin/"),
             name='root-redirect'),
    )

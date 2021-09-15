"""StudentiUniMi URL Configuration

The `urlpatterns` list routes URLs to views.
"""
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from django.views.generic import RedirectView

import telegrambot.urls
import university.urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(university.urls)),
    path('telegrambot/', include(telegrambot.urls)),
    url(r'^robots.txt$', lambda r: HttpResponse(
        "User-Agent: *\nDisallow: /",
        content_type="text/plain",
    ), name="robots_txt"),
]

if not settings.DEBUG:
    urlpatterns.append(
        path('', RedirectView.as_view(url="https://api.studentiunimi.it/admin/"),
             name='root-redirect'),
    )

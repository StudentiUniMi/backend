"""StudentiUniMi URL Configuration

The `urlpatterns` list routes URLs to views.
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

import telegrambot.urls
import university.urls
import university.views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(university.urls)),
    path('telegrambot/', include(telegrambot.urls)),
    path('parse-json-data/', include(university.urls)),
]

if not settings.DEBUG:
    urlpatterns.append(
        path('', RedirectView.as_view(url="https://github.com/StudentiUniMi/backend"),
             name='github-redirect'),
    )


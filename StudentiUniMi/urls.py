"""StudentiUniMi URL Configuration

The `urlpatterns` list routes URLs to views.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

import university.views

router = routers.DefaultRouter()
router.register(r"degrees", university.views.DegreeViewSet, basename="Degree")
router.register(r"departments", university.views.DepartmentViewSet, basename="Department")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]

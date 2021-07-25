from django.contrib import admin
from university.models import (
    Department,
    Degree,
    Course,
)


@admin.register(Department, Degree, Course)
class BaseAdmin(admin.ModelAdmin):
    pass

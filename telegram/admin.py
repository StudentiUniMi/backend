from django.contrib import admin
from telegram.models import (
    User,
    Group,
)


@admin.register(User, Group)
class BaseAdmin(admin.ModelAdmin):
    pass

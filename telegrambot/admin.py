from django.contrib import admin
from telegrambot.models import (
    User,
    Group,
    GroupMembership,
    TelegramBot,
)


class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 1


class GroupOwnerFilter(admin.SimpleListFilter):
    title = "owner"
    parameter_name = "owner"

    def lookups(self, request, model_admin):
        groups = Group.objects.all()
        return (
            (g.pk, g.owner) for g in groups
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(owner=self.value())


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("__str__", "reputation", "warn_count", "banned", "permissions_level", )
    search_fields = ("id", "first_name", "last_name", )
    fields = ("id", "first_name", "last_name", "username", "reputation", "warn_count", "banned", "permissions_level", "last_seen", )
    inlines = (GroupMembershipInline, )


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("__str__", "owner", )
    list_filter = (GroupOwnerFilter, )
    search_fields = ("title", )
    fields = ("id", "title", "description", "profile_picture", "invite_link", "owner", )
    inlines = (GroupMembershipInline, )


@admin.register(TelegramBot)
class TelegramBotAdmin(admin.ModelAdmin):
    list_display = ("username", "censured_token", "notes")
    fields = ("token", "notes")

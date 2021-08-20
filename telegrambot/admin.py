from django.contrib import admin

from telegrambot.models import (
    User,
    Group,
    GroupMembership,
    TelegramBot, UserPrivilege,
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
    list_display = ("__str__", "reputation", "warn_count", "banned", "verified", "permissions_level", )
    search_fields = ("id", "first_name", "last_name", )
    fields = ("id", "first_name", "last_name", "username", "reputation", "warn_count", "banned", "permissions_level",
              "last_seen", "verified", )
    inlines = (GroupMembershipInline, )


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("__str__", "owner", )
    list_filter = (GroupOwnerFilter, )
    search_fields = ("title", )
    fields = ("id", "title", "description", "profile_picture", "invite_link", "owner", "bot", "welcome_model", )
    inlines = (GroupMembershipInline, )


@admin.register(UserPrivilege)
class UserPrivilegeAdmin(admin.ModelAdmin):
    list_display = ("user", "type", "scope", )
    fieldsets = (
        (None, {
            "fields": ("user", "type", )
        }),
        ("Authorization", {
            "fields": ("scope", "authorized_groups", "authorized_degrees", "authorized_departments"),
        }),
        ("Telegram privileges", {
            "classes": ("collapse", ),
            "fields": ("custom_title", "can_change_info", "can_invite_users", "can_pin_messages", "can_manage_chat",
                       "can_delete_messages", "can_manage_voice_chats", "can_restrict_members",
                       "can_promote_members", ),
        })
    )


@admin.register(TelegramBot)
class TelegramBotAdmin(admin.ModelAdmin):
    list_display = ("username", "censured_token", "notes")
    fields = ("token", "notes")

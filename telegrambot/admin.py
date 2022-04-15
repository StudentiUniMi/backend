from datetime import datetime

import asyncio
import telegram.error
import telethon.errors
import time
from django.conf import settings
from django.contrib import admin
from django.core.checks import messages
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import (
    EditAdminRequest,
    CreateChannelRequest,
    InviteToChannelRequest,
)
from telethon.tl.types import ChatAdminRights

from telegrambot.models import (
    User,
    Group,
    GroupMembership,
    TelegramBot,
    UserPrivilege,
    TelegramUserbot,
    BotWhitelist,
    TelegramLog,
    BlacklistedUser,
)


class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 1
    autocomplete_fields = ("group", "user", )


class UserLogInline(admin.TabularInline):
    model = TelegramLog
    fk_name = "target"
    extra = 0
    fields = ("iso_timestamp", "event", "chat", "issuer", )
    readonly_fields = ("iso_timestamp", )
    show_change_link = True
    ordering = ("-timestamp", )

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj):
        return False


class GroupOwnerFilter(admin.SimpleListFilter):
    title = "owner"
    parameter_name = "owner"

    def lookups(self, request, model_admin):
        groups = Group.objects.all()
        result = [
            ("no-owner", "No owner"),
        ]
        for g in groups:
            if g.owner:
                result.append((g.owner.id, str(g.owner)))
        return list(dict.fromkeys(result))

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        if self.value() == "no-owner":
            return queryset.filter(owner=None)
        return queryset.filter(owner=self.value())


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("name", "id", "reputation", "warn_count", "banned", "permissions_level", )
    search_fields = ("id", "first_name", "last_name", "username", )
    fields = ("id", "first_name", "last_name", "username", "reputation", "warn_count", "banned", "permissions_level",
              "last_seen", )
    inlines = (GroupMembershipInline, UserLogInline, )


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    @staticmethod
    def create_telegram_group(group, bot):
        userbot: TelegramUserbot = TelegramUserbot.objects.all()\
            .filter(active=True)\
            .prefetch_related("user")\
            .order_by("-last_used")\
            .first()
        file_path = f"media/{userbot.session_file.name}"

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        with TelegramClient(file_path, settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH) as client:
            mtbot = client.get_input_entity(bot.username)

            response = client(CreateChannelRequest(
                title=group.title,
                about=group.description,
                broadcast=False,
                megagroup=True,
            ))
            if len(response.chats) < 1:
                return {"ok": False}

            mtgroup = response.chats[0]
            client(InviteToChannelRequest(
                channel=mtgroup,
                users=[mtbot, ]
            ))
            client(EditAdminRequest(
                channel=mtgroup,
                user_id=mtbot.user_id,
                admin_rights=ChatAdminRights(
                    change_info=True,
                    delete_messages=True,
                    ban_users=True,
                    invite_users=True,
                    pin_messages=True,
                    add_admins=True,
                    manage_call=True,
                    other=True,
                ),
                rank="Bot",
            ))

            userbot.last_used = datetime.now()
            userbot.group_count += 1
            userbot.save()
            return int(f"-100{mtgroup.id}")

    @admin.action(description="Fetch and update Telegram data")
    def fetch_telegram_info_action(self, request, queryset):
        stats = {False: 0, True: 0}
        for group in queryset:
            try:
                stats[group.update_info()] += 1
            except telegram.error.RetryAfter as e:
                time.sleep(e.retry_after + 1)
        self.message_user(request, f"{stats[True]} groups updated.\n{stats[False]} groups not updated.")

    def save_model(self, request, obj: Group, form, change):
        if obj.id == 0:
            try:
                obj.id = self.create_telegram_group(
                    group=obj,
                    bot=obj.bot,
                )
                obj.save()
            except telethon.errors.RPCError as e:
                self.message_user(
                    request, f"Can't create the group. Telethon error: {e.message}",
                    level=messages.ERROR,
                )
                return

        if not obj.update_info():
            super(GroupAdmin, self).save_model(request, obj, form, change)
            self.message_user(
                request, f"The group has been saved, but the bot was not able to retrieve any data from Telegram.\n"
                         f"Are you sure you inserted the correct chat id and selected the right bot?",
                level=messages.WARNING,
            )

    list_display = ("id", "title", "owner", )
    list_filter = (GroupOwnerFilter, )
    search_fields = ("id", "title", )
    fields = ("id", "title", "description", "profile_picture", "invite_link", "owner", "bot", "welcome_model",
              "ignore_admin_tagging", )
    autocomplete_fields = ("owner", "bot", )
    actions = [fetch_telegram_info_action, ]


@admin.register(UserPrivilege)
class UserPrivilegeAdmin(admin.ModelAdmin):
    list_display = ("user", "type", "custom_title", "scope", )
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
                       "can_promote_members", "can_superban_members", ),
        })
    )
    autocomplete_fields = ("user", "authorized_groups", "authorized_degrees", "authorized_departments", )


@admin.register(TelegramBot)
class TelegramBotAdmin(admin.ModelAdmin):
    list_display = ("username", "censured_token", "notes")
    search_fields = ("username", )
    fields = ("token", "notes")


@admin.register(TelegramUserbot)
class TelegramUserbotAdmin(admin.ModelAdmin):
    list_display = ("user", "active", "group_count", "last_used")
    search_fields = ("user", "user__first_name", "user__last_name", "user__username", )
    fields = ("user", "session_file", "active", "group_count", "last_used", )
    autocomplete_fields = ("user", )


@admin.register(BotWhitelist)
class BotWhitelistAdmin(admin.ModelAdmin):
    list_display = ("username", "whitelisted_by")
    search_fields = ("username", "whitelisted_by")


@admin.register(TelegramLog)
class TelegramLogAdmin(admin.ModelAdmin):
    list_display = ("iso_timestamp", "event", "chat", "target", "issuer", )
    search_fields = [
        "issuer__id",
        "issuer__username",
        "issuer__first_name",
        "issuer__last_name",
        "target__id",
        "target__username",
        "target__first_name",
        "target__last_name",
        "chat__title",
        "chat__id",
    ]
    list_filter = ("event", )
    date_hierarchy = "timestamp"
    ordering = ["-timestamp"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(BlacklistedUser)
class BlacklistedUserAdmin(admin.ModelAdmin):
    list_display = ("user_id", "source")
    search_fields = ["user_id", ]
    list_filter = ("source", )

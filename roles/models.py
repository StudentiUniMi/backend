from django.db import models
from polymorphic.models import PolymorphicModel

from telegrambot.handlers import utils
from telegrambot.logging import (
    EventTypes,
    MODERATION_INFO,
    MODERATION_DEL,
    MODERATION_WARN,
    MODERATION_KICK,
    MODERATION_BAN,
    MODERATION_MUTE,
    MODERATION_FREE,
    MODERATION_SUPERBAN,
    MODERATION_SUPERFREE,
)


class BaseRole(PolymorphicModel):
    """Abstract class for all roles"""
    class Meta:
        verbose_name = "Staff member"
        verbose_name_plural = "Staff members"

    tg_user = models.ForeignKey("telegrambot.User", on_delete=models.CASCADE)
    django_user = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True, blank=True)

    # Permissions scope
    all_groups = models.BooleanField("All groups", default=False)
    extra_groups = models.BooleanField("Extra groups", default=False, help_text="Groups without an associated degree")
    degrees = models.ManyToManyField("university.Degree", related_name="roles", blank=True)

    # Custom title override
    custom_title_override = models.CharField("Custom title", max_length=16, blank=True, null=True)

    # Moderation permissions overrides
    moderation_info = models.BooleanField(
        help_text="/info command",
        null=True, blank=True, default=None,
    )
    moderation_del = models.BooleanField(
        help_text="/del command",
        null=True, blank=True, default=None,
    )
    moderation_warn = models.BooleanField(
        help_text="/warn command",
        null=True, blank=True, default=None,
    )
    moderation_kick = models.BooleanField(
        help_text="/kick command",
        null=True, blank=True, default=None,
    )
    moderation_ban = models.BooleanField(
        help_text="/ban command",
        null=True, blank=True, default=None,
    )
    moderation_mute = models.BooleanField(
        help_text="/mute command",
        null=True, blank=True, default=None,
    )
    moderation_free = models.BooleanField(
        help_text="/free command",
        null=True, blank=True, default=None,
    )
    moderation_superban = models.BooleanField(
        help_text="/superban command",
        null=True, blank=True, default=None,
    )
    moderation_superfree = models.BooleanField(
        help_text="/superfree command",
        null=True, blank=True, default=None,
    )

    # Telegram permissions overrides
    can_change_info = models.BooleanField(
        help_text="True, if the user is allowed to change the chat title, photo and other settings",
        null=True, blank=True, default=None,
    )
    can_invite_users = models.BooleanField(
        help_text="True, if the user is allowed to invite new users to the chat",
        null=True, blank=True, default=None,
    )
    can_pin_messages = models.BooleanField(
        help_text="True, if the user is allowed to pin messages; groups and supergroups only",
        null=True, blank=True, default=None,
    )
    can_manage_chat = models.BooleanField(
        help_text="True, if the administrator can access the chat event log, chat statistics, message statistics in "
                  "channels, see channel members, see anonymous administrators in supergroups and ignore slow mode. "
                  "Implied by any other administrator privilege",
        null=True, blank=True, default=None,
    )
    can_delete_messages = models.BooleanField(
        help_text="True, if the administrator can delete messages of other users",
        null=True, blank=True, default=None,
    )
    can_manage_voice_chats = models.BooleanField(
        help_text="True, if the administrator can manage voice chats",
        null=True, blank=True, default=None,
    )
    can_restrict_members = models.BooleanField(
        help_text="True, if the administrator can restrict, ban or unban chat members",
        null=True, blank=True, default=None,
    )
    can_promote_members = models.BooleanField(
        help_text="True, if the administrator can add new administrators with a subset of their own privileges or "
                  "demote administrators that he has promoted, directly or indirectly "
                  "(promoted by administrators that were appointed by the user)",
        null=True, blank=True, default=None,
    )

    def permissions(self) -> list[EventTypes | None]:
        return [
            MODERATION_INFO if self.moderation_info else None,
            MODERATION_DEL if self.moderation_del else None,
            MODERATION_WARN if self.moderation_warn else None,
            MODERATION_KICK if self.moderation_kick else None,
            MODERATION_BAN if self.moderation_ban else None,
            MODERATION_MUTE if self.moderation_mute else None,
            MODERATION_FREE if self.moderation_free else None,
            MODERATION_SUPERBAN if self.moderation_superban else None,
            MODERATION_SUPERFREE if self.moderation_superfree else None,
        ]

    def telegram_permissions(self) -> dict[str, bool]:
        return {
            "can_change_info": self.can_change_info if self.can_change_info is not None else False,
            "can_invite_users": self.can_invite_users if self.can_invite_users is not None else False,
            "can_pin_messages": self.can_pin_messages if self.can_pin_messages is not None else False,
            "can_manage_chat": self.can_manage_chat if self.can_manage_chat is not None else False,
            "can_delete_messages": self.can_delete_messages if self.can_delete_messages is not None else False,
            "can_manage_voice_chats": self.can_manage_voice_chats if self.can_manage_voice_chats is not None else False,
            "can_restrict_members": self.can_restrict_members if self.can_restrict_members is not None else False,
            "can_promote_members": self.can_promote_members if self.can_restrict_members is not None else False,
        }

    def custom_title(self) -> str | None:
        return self.custom_title_override

    def polymorphic_type(self) -> str:
        return str(self.polymorphic_ctype).split('|')[1].lstrip()
    polymorphic_type.short_description = "Role"

    def __str__(self) -> str:
        return f"{self.polymorphic_type()} {self.tg_user.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        groups = self.tg_user.member_of.all()
        for group in groups:
            utils.set_admin_rights(self.tg_user, group, force=True)

    def delete(self, *args, **kwargs):
        groups = self.tg_user.member_of.all()
        super().delete(*args, **kwargs)
        for group in groups:
            utils.set_admin_rights(self.tg_user, group, force=True)


class Representative(BaseRole):
    class Meta:
        verbose_name = "Representative"
        verbose_name_plural = "Representatives"

    political_list = models.CharField("Political list", max_length=16)
    political_role = models.CharField("Political role", max_length=16)

    def permissions(self) -> list[EventTypes | None]:
        return super().permissions()

    def telegram_permissions(self) -> dict[str, bool]:
        perms = super().telegram_permissions()
        perms["can_pin_messages"] = self.can_pin_messages if self.can_pin_messages is not None else True
        return perms

    def custom_title(self) -> str:
        if super().custom_title():
            return super().custom_title()
        return f"{self.political_role + ' ' if self.political_role else ''}{self.political_list}"

    def __str__(self) -> str:
        return f"{super().__str__()} ({self.political_list})"


class Professor(BaseRole):
    class Meta:
        verbose_name = "Professor"
        verbose_name_plural = "Professors"

    def permissions(self) -> list[EventTypes | None]:
        return super().permissions()

    def telegram_permissions(self) -> dict[str, bool]:
        perms = super().telegram_permissions()
        perms["can_pin_messages"] = self.can_pin_messages if self.can_pin_messages is not None else True
        return perms

    def custom_title(self) -> str | None:
        if super().custom_title():
            return super().custom_title()
        return "Docente"


class Moderator(BaseRole):
    class Meta:
        verbose_name = "Moderator"
        verbose_name_plural = "Moderators"

    def permissions(self) -> list[EventTypes | None]:
        return [
            *super().permissions(),
            MODERATION_INFO if self.moderation_info is not False else None,
            MODERATION_DEL if self.moderation_del is not False else None,
            MODERATION_MUTE if self.moderation_mute is not False else None,
        ]

    def telegram_permissions(self) -> dict[str, bool]:
        perms = super().telegram_permissions()
        perms["can_pin_messages"] = self.can_pin_messages if self.can_pin_messages is not None else True
        perms["can_manage_chat"] = self.can_manage_chat if self.can_manage_chat is not None else True
        return perms

    def custom_title(self) -> str | None:
        if super().custom_title():
            return super().custom_title()
        return "Moderatore"


class Administrator(BaseRole):
    class Meta:
        verbose_name = "Administrator"
        verbose_name_plural = "Administrators"

    def permissions(self) -> list[EventTypes | None]:
        return [
            *super().permissions(),
            MODERATION_INFO if self.moderation_info is not False else None,
            MODERATION_DEL if self.moderation_del is not False else None,
            MODERATION_WARN if self.moderation_warn is not False else None,
            MODERATION_KICK if self.moderation_kick is not False else None,
            MODERATION_MUTE if self.moderation_mute is not False else None,
            MODERATION_BAN if self.moderation_ban is not False else None,
            MODERATION_FREE if self.moderation_free is not False else None,
        ]

    def telegram_permissions(self) -> dict[str, bool]:
        perms = super().telegram_permissions()
        perms["can_pin_messages"] = self.can_pin_messages if self.can_pin_messages is not None else True
        perms["can_change_info"] = self.can_change_info if self.can_change_info is not None else True
        return perms

    def custom_title(self) -> str | None:
        if super().custom_title():
            return super().custom_title()
        return "Amministratore"


class SuperAdministrator(BaseRole):
    class Meta:
        verbose_name = "Super Administrator"
        verbose_name_plural = "Super Administrators"

    def permissions(self) -> list[EventTypes | None]:
        return [
            MODERATION_INFO if self.moderation_info is not False else None,
            MODERATION_DEL if self.moderation_del is not False else None,
            MODERATION_WARN if self.moderation_warn is not False else None,
            MODERATION_KICK if self.moderation_kick is not False else None,
            MODERATION_MUTE if self.moderation_mute is not False else None,
            MODERATION_BAN if self.moderation_ban is not False else None,
            MODERATION_FREE if self.moderation_free is not False else None,
            MODERATION_SUPERBAN if self.moderation_superban is not False else None,
            MODERATION_SUPERFREE if self.moderation_superfree is not False else None,
        ]

    def telegram_permissions(self) -> dict[str, bool]:
        return {
            "can_change_info": self.can_change_info if self.can_change_info is not None else True,
            "can_invite_users": self.can_invite_users if self.can_invite_users is not None else True,
            "can_pin_messages": self.can_pin_messages if self.can_pin_messages is not None else True,
            "can_manage_chat": self.can_manage_chat if self.can_manage_chat is not None else True,
            "can_delete_messages": self.can_delete_messages if self.can_delete_messages is not None else True,
            "can_manage_voice_chats": self.can_manage_voice_chats if self.can_manage_voice_chats is not None else True,
            "can_restrict_members": self.can_restrict_members if self.can_restrict_members is not None else True,
            "can_promote_members": self.can_promote_members if self.can_restrict_members is not None else True,
        }

    def custom_title(self) -> str | None:
        if super().custom_title():
            return super().custom_title()
        return "CdA Network"

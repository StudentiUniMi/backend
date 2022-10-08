from datetime import datetime
from enum import Enum

import telegram
from telegram import Message, Chat
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class EventTypes(Enum):
    CHAT_DOES_NOT_EXIST = 0, '❗️', None
    MODERATION_INFO = 5, 'ℹ️', None
    MODERATION_WARN = 1, '🟡', _("warned")
    MODERATION_KICK = 2, '⚪', _("banned from the group")
    MODERATION_BAN = 3, '🔴', _("permanently banned from the group")
    MODERATION_MUTE = 4, '🟠', _("muted in the group")
    MODERATION_FREE = 6, '🟢', _("unbanned from the group")
    MODERATION_SUPERBAN = 7, '⚫️', _("permanently banned from all groups")
    MODERATION_SUPERFREE = 11, '✳️', _("unbanned from all groups")
    USER_JOINED = 8, '➕', None
    USER_LEFT = 9, '➖', None
    NOT_ENOUGH_RIGHTS = 10, '🔰', None
    TELEGRAM_ERROR = 12, '❗️', None
    USER_CALLED_ADMIN = 13, '🧑‍⚖️', None
    MODERATION_DEL = 14, '✏️', None
    WHITELIST_BOT = 15, '⚪', None
    BROADCAST = 16, '📡', None

    @property
    def command(self) -> str:
        if "MODERATION_" not in self.name:
            return ''
        return '_'.join(self.name.split("_")[1:]).lower()


CHAT_DOES_NOT_EXIST = EventTypes.CHAT_DOES_NOT_EXIST
MODERATION_INFO = EventTypes.MODERATION_INFO
MODERATION_WARN = EventTypes.MODERATION_WARN
MODERATION_KICK = EventTypes.MODERATION_KICK
MODERATION_BAN = EventTypes.MODERATION_BAN
MODERATION_MUTE = EventTypes.MODERATION_MUTE
MODERATION_FREE = EventTypes.MODERATION_FREE
MODERATION_SUPERBAN = EventTypes.MODERATION_SUPERBAN
MODERATION_SUPERFREE = EventTypes.MODERATION_SUPERFREE
USER_JOINED = EventTypes.USER_JOINED
USER_LEFT = EventTypes.USER_LEFT
NOT_ENOUGH_RIGHTS = EventTypes.NOT_ENOUGH_RIGHTS
TELEGRAM_ERROR = EventTypes.TELEGRAM_ERROR
WHITELIST_BOT = EventTypes.WHITELIST_BOT
USER_CALLED_ADMIN = EventTypes.USER_CALLED_ADMIN
MODERATION_DEL = EventTypes.MODERATION_DEL
BROADCAST = EventTypes.BROADCAST


def _normalize_group_id(group_id) -> str:
    if not group_id:
        return "#gid_unknown"
    return f"#gid_{str(group_id).replace('-', '')}"


def _normalize_user_id(user_id) -> str:
    if not user_id:
        return "#uid_unknown"
    return f"#uid_{user_id}"


def _format_chat(chat) -> str:
    if not chat:
        return ""
    return f"{getattr(chat, 'title')} {_normalize_group_id(getattr(chat, 'id'))}"


def _format_user(user) -> str:
    if not user:
        return ""

    text = f"{getattr(user, 'first_name')}"
    if getattr(user, "last_name"):
        text += f" {user.last_name}"
    if getattr(user, "username"):
        text += f" [{'@' if user.username[0] != '@' else ''}{user.username}]"

    return f"{text} {_normalize_user_id(getattr(user, 'id'))}"


def prepare(msg: Message = None) -> Message:
    """Prepare a log entry before executing an action.
    Useful for commands like /del to log the deleted message before it disappears.

    :param msg: the message that prompted the action
    :return: a message to pass to log
    """
    bot = telegram.Bot(settings.LOGGING_BOT_TOKEN)
    sent_msg: Message = bot.send_message(chat_id=settings.LOGGING_CHAT_ID, text="...", parse_mode="html")

    if msg:
        msg.forward(chat_id=settings.LOGGING_CHAT_ID)
    return sent_msg


def log_db_save(
        event: EventTypes,
        chat: Chat | None,
        target=None,
        issuer=None,
        reason=None,
        error_message=None,
        msg: Message = None,
        msg_deleted: bool = None,
) -> None:
    """Save event onto DB"""
    from telegrambot.models import (
        TelegramLog,
        User as DBUser,
        Group as DBGroup,
    )  # Circular import

    db_log = TelegramLog()
    db_log.event = event.value[0]
    db_log.timestamp = datetime.now()
    if chat:
        db_log.chat = DBGroup.objects.get(id=chat.id)
    if target:
        db_log.target = DBUser.objects.get(id=target.id)
    if issuer:
        db_log.issuer = DBUser.objects.get(id=issuer.id)
    if reason:
        db_log.reason = reason
    if error_message and not reason:
        db_log.reason = error_message
    if msg:
        db_log.message = msg.text_markdown_v2
        db_log.message_deleted = bool(msg_deleted)
    db_log.save()


def log(
        event: EventTypes,
        chat: Chat | None,
        target=None,
        issuer=None,
        reason=None,
        bot=None,
        msg: Message = None,
        target_message_deleted: bool = None,
        prepared_entry: Message = None,
        **kwargs
) -> None:
    """Log an event to the log chat.

    :param event: must be an instance of `telegrambot.logging.EventTypes`
    :param chat: the chat where the event was generated
    :param target: the target user
    :param issuer: the command issuer (only for moderation events)
    :param reason: admin-specified reason for the action (only for moderation events)
    :param bot: like target but when the target is not a user but a bot
    :param msg: the message that prompted the action
    :param target_message_deleted: True if the message was deleted after the default action (with a /...* command)
    :param prepared_entry: the output of the logging.prepare function
    :return: None
    """
    error_message = kwargs.get("error_message", False)
    log_db_save(
        event,
        chat,
        target=target,
        issuer=issuer,
        reason=reason,
        msg=msg,
        msg_deleted=target_message_deleted,
        error_message=error_message if error_message else None,
    )

    text = f"{event.value[1]} #{event.name}{'*' if target_message_deleted else ''}"
    if chat is not None:
        text += f"\n👥 <b>Group</b>: {_format_chat(chat)}"

    if event in [
        EventTypes.MODERATION_WARN,
        EventTypes.MODERATION_KICK,
        EventTypes.MODERATION_BAN,
        EventTypes.MODERATION_MUTE,
        EventTypes.MODERATION_FREE,
        EventTypes.MODERATION_SUPERBAN,
        EventTypes.MODERATION_SUPERFREE,
        EventTypes.MODERATION_DEL,
        EventTypes.USER_LEFT,
        EventTypes.USER_JOINED,
        EventTypes.NOT_ENOUGH_RIGHTS,
        EventTypes.USER_CALLED_ADMIN,
    ] and target is not None:
        text += f"\n👤 <b>Target user</b>: {_format_user(target)}"
    if event in [EventTypes.WHITELIST_BOT, ]:
        if not bot:
            return
        text += f"\n👤 <b>Target bot</b>: {bot.user.username}"  # bot is an object of the telegram library
    if event in [
        EventTypes.MODERATION_WARN,
        EventTypes.MODERATION_KICK,
        EventTypes.MODERATION_BAN,
        EventTypes.MODERATION_MUTE,
        EventTypes.MODERATION_FREE,
        EventTypes.MODERATION_SUPERBAN,
        EventTypes.MODERATION_SUPERFREE,
        EventTypes.WHITELIST_BOT,
        EventTypes.MODERATION_DEL,
        EventTypes.USER_CALLED_ADMIN,
        EventTypes.BROADCAST,
    ]:
        text += f"\n👮 <b>Issuer</b>: {_format_user(issuer)}"
    if event in [
        EventTypes.MODERATION_MUTE,
    ] and kwargs.get("until_date", False):
        until_date: datetime = kwargs["until_date"]
        text += f"\n⏳ <b>Until date</b>: {until_date.strftime('%d/%m/%Y %H:%M')}"
    if event in [
        EventTypes.TELEGRAM_ERROR
    ] and kwargs.get("error_message", False):
        text += f"\n💬 <b>Error message</b>: {kwargs['error_message']}"
    if reason:
        text += f"\n💬 <b>Reason</b>: {reason}"
    if msg:
        text += f"\n📜 <b>Message</b>: <i>see below</i>"

    bot = telegram.Bot(settings.LOGGING_BOT_TOKEN)
    if not prepared_entry:
        bot.send_message(chat_id=settings.LOGGING_CHAT_ID, text=text, parse_mode="html")
    else:
        prepared_entry.edit_text(text=text, parse_mode="html")

    if msg and not prepared_entry:
        try:
            msg.forward(chat_id=settings.LOGGING_CHAT_ID)
        except telegram.TelegramError:
            pass

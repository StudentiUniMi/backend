from datetime import datetime
from enum import Enum

import telegram
from django.conf import settings


class EventTypes(Enum):
    CHAT_DOES_NOT_EXIST = 0, '❗️'
    MODERATION_WARN = 1, '🟡'
    MODERATION_KICK = 2, '⚪'
    MODERATION_BAN = 3, '🔴'
    MODERATION_MUTE = 4, '🟠'
    MODERATION_FREE = 6, '🟢'
    MODERATION_SUPERBAN = 7, '⚫️'
    MODERATION_SUPERFREE = 11, '✳️'
    USER_JOINED = 8, '➕'
    USER_LEFT = 9, '➖'
    NOT_ENOUGH_RIGHTS = 10, '🔰'


CHAT_DOES_NOT_EXIST = EventTypes.CHAT_DOES_NOT_EXIST
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
        text += f" [{'@' if user.username[0] is not '@' else ''}{user.username}]"

    return f"{text} {_normalize_user_id(getattr(user, 'id'))}"


def log(event: EventTypes, chat, target=None, issuer=None, **kwargs) -> None:
    """Log an event to the log chat.

    :param event: must be an instance of `telegrambot.logging.EventTypes`
    :param chat: the chat where the event was generated
    :param target: the target user
    :param issuer: the command issuer (only for moderation events)
    :return: None
    """

    text = f"{event.value[1]} #{event.name}"
    text += f"\n👥 <b>Group</b>: {_format_chat(chat)}"

    if event in [
        EventTypes.MODERATION_WARN,
        EventTypes.MODERATION_KICK,
        EventTypes.MODERATION_BAN,
        EventTypes.MODERATION_MUTE,
        EventTypes.MODERATION_FREE,
        EventTypes.MODERATION_SUPERBAN,
        EventTypes.MODERATION_SUPERFREE,
        EventTypes.USER_LEFT,
        EventTypes.USER_JOINED,
        EventTypes.NOT_ENOUGH_RIGHTS,
    ]:
        text += f"\n👤 <b>Target user</b>: {_format_user(target)}"
    if event in [
        EventTypes.MODERATION_WARN,
        EventTypes.MODERATION_KICK,
        EventTypes.MODERATION_BAN,
        EventTypes.MODERATION_MUTE,
        EventTypes.MODERATION_FREE,
        EventTypes.MODERATION_SUPERBAN,
        EventTypes.MODERATION_SUPERFREE,
    ]:
        text += f"\n👮 <b>Issuer</b>: {_format_user(issuer)}"
    if event in [
        EventTypes.MODERATION_MUTE,
    ] and kwargs.get("until_date", False):
        until_date: datetime = kwargs["until_date"]
        text += f"\n⏳ <b>Until date</b>: {until_date.strftime('%d/%m/%Y %H:%M')}"

    bot = telegram.Bot(settings.LOGGING_BOT_TOKEN)
    bot.send_message(chat_id=settings.LOGGING_CHAT_ID, text=text, parse_mode="html")

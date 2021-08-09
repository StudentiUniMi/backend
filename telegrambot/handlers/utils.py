from datetime import datetime

import telegram
from django.apps import apps
from telegram import Bot, User, Chat, TelegramError
from telegram.ext import DispatcherHandlerStop


def get_bot(chat: Chat) -> telegram.Bot:
    DBGroup = apps.get_model("telegrambot.Group")
    if isinstance(chat, DBGroup):
        dbgroup = chat
    else:
        dbgroup = DBGroup.objects.get(id=chat.id)
    bot = telegram.Bot(dbgroup.bot.token)
    return bot


def save_user(user: User, chat: Chat, bot: Bot):
    """
    Saves (or updates) an user (in a group) in the database.
    """
    DBUser = apps.get_model("telegrambot.User")
    dbuser = DBUser.objects.update_or_create(
        id=user.id,
        defaults={
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "last_seen": datetime.now(),
        }
    )[0]
    if dbuser.banned:
        # The user is globally banned from the network
        bot.ban_chat_member(
            chat_id=chat.id,
            user_id=user.id,
        )
        raise DispatcherHandlerStop

    DBGroupMembership = apps.get_model("telegrambot.GroupMembership")
    dbmembership = DBGroupMembership.objects.update_or_create(
        user_id=user.id,
        group_id=chat.id,
        defaults={
            "last_seen": datetime.now(),
        }
    )[0]
    dbmembership.messages_count += 1
    dbmembership.save()
    return dbuser


def set_admin_rights(dbuser, chat):
    privileges = dbuser.get_privileges(chat)
    if not privileges:
        return

    bot = get_bot(chat)
    try:
        bot.promote_chat_member(
            chat_id=chat.id,
            user_id=dbuser.id,
            can_change_info=privileges.can_change_info,
            can_delete_messages=privileges.can_delete_messages,
            can_invite_users=privileges.can_invite_users,
            can_restrict_members=privileges.can_restrict_members,
            can_pin_messages=privileges.can_pin_messages,
            can_promote_members=privileges.can_promote_members,
            can_manage_chat=privileges.can_manage_chat,
            can_manage_voice_chats=privileges.can_manage_voice_chats,
        )
        bot.set_chat_administrator_custom_title(
            chat_id=chat.id,
            user_id=dbuser.id,
            custom_title=privileges.custom_title,
        )
    except TelegramError:
        # The bot has no enough rights
        # TODO: Alert administrators
        pass


def remove_admin_rights(dbuser, chat: Chat):
    bot = get_bot(chat)
    try:
        bot.promote_chat_member(
            chat_id=chat.id,
            user_id=dbuser.id,
            can_change_info=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False,
            can_manage_chat=False,
            can_manage_voice_chats=False,
        )
    except TelegramError:
        # The bot has no enough rights
        # TODO: Alert administrators
        pass

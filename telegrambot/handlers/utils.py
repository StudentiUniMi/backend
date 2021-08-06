from datetime import datetime

from telegram import Bot, User, Chat
from telegram.ext import DispatcherHandlerStop

from telegrambot.models import (
    User as DBUser,
    GroupMembership as DBGroupMembership,
)


def save_user(user: User, chat: Chat, bot: Bot) -> None:
    """
    Saves (or updates) an user (in a group) in the database.
    """
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

    dbmembership = DBGroupMembership.objects.update_or_create(
        user_id=user.id,
        group_id=chat.id,
        defaults={
            "last_seen": datetime.now(),
        }
    )[0]
    dbmembership.messages_count += 1
    dbmembership.save()

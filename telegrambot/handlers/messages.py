from datetime import datetime

from telegram import Update, User, Message, Chat
from telegram.ext import CallbackContext

from telegrambot.models import (
    User as DBUser,
    Group as DBGroup,
    GroupMembership as DBGroupMembership,
)


def group_messages_handler(update: Update, context: CallbackContext) -> None:
    """
    Handles a message in a group by updating the database
    """
    message: Message = update.message
    sender: User = message.from_user
    chat: Chat = message.chat

    if sender.id == context.bot.id:
        return  # Ignore messages sent by the bot

    dbuser = DBUser.objects.update_or_create(
        id=sender.id,
        defaults={
            "first_name": sender.first_name,
            "last_name": sender.last_name,
            "username": sender.username,
            "last_seen": datetime.now(),
        }
    )[0]
    if dbuser.banned:
        context.bot.ban_chat_member(
            chat_id=chat.id,
            user_id=sender.id,
        )
        return

    DBGroup.objects.update_or_create(
        id=chat.id,
        defaults={
            "title": chat.title,
        }
    )
    dbmembership = DBGroupMembership.objects.update_or_create(
        user_id=sender.id,
        group_id=chat.id,
        defaults={
            "last_seen": datetime.now(),
        }
    )[0]
    dbmembership.messages_count += 1
    dbmembership.save()

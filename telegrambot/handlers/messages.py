from datetime import datetime

from telegram import Update, User, Message, Chat
from telegram.ext import CallbackContext
from telegram.ext.dispatcher import DispatcherHandlerStop

from telegrambot.models import (
    User as DBUser,
    Group as DBGroup,
    GroupMembership as DBGroupMembership,
)


def handle_group_messages(update: Update, context: CallbackContext) -> None:
    """
    Handles a message in a group by updating the database
    """
    message: Message = update.message
    sender: User = message.from_user
    chat: Chat = message.chat

    if sender.id == context.bot.id:
        # Ignore messages sent by the bot itself
        raise DispatcherHandlerStop

    try:
        dbgroup = DBGroup.objects.get(id=chat.id)
        dbgroup.title = chat.title
        dbgroup.save(force_update=True, update_fields=["title", ])
    except DBGroup.DoesNotExist:
        # The group is not in the database; ignore all updates from it
        # TODO: Log this thing somewhere
        raise DispatcherHandlerStop

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
        # The user is globally banned from the network
        context.bot.ban_chat_member(
            chat_id=chat.id,
            user_id=sender.id,
        )
        raise DispatcherHandlerStop

    dbmembership = DBGroupMembership.objects.update_or_create(
        user_id=sender.id,
        group_id=chat.id,
        defaults={
            "last_seen": datetime.now(),
        }
    )[0]
    dbmembership.messages_count += 1
    dbmembership.save()

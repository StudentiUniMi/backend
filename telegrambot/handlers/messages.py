from telegram import Update, User, Message, Chat, ChatPermissions
from telegram.ext import CallbackContext, DispatcherHandlerStop

from telegrambot import logging
from telegrambot.handlers import utils
from telegrambot.models import (
    Group as DBGroup,
    User as DBUser,
)
from telegrambot.handlers import members


def handle_group_messages(update: Update, context: CallbackContext) -> None:
    """Handle a message in a group by updating the database.

    :raises: DispatcherHandlerStop if the messages comes from the bot itself or
    the group does not exists in the database.
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
        logging.log(logging.CHAT_DOES_NOT_EXIST, chat)
        context.bot.leave_chat(chat_id=chat.id)
        raise DispatcherHandlerStop

    # This could probably be done better
    if len(update.message.new_chat_members) == 0 and update.message.left_chat_member is None:
        try:
            dbuser: DBUser = DBUser.objects.get(id=sender.id)
            found = False
            if not dbuser.verified:
                for member in context.bot.get_chat_administrators(chat.id):
                    if member.user.id == sender.id:
                        dbuser.verified = True
                        dbuser.save()
                        found = True
                        break
                if not found:
                    context.bot.restrict_chat_member(chat.id, sender.id, ChatPermissions(can_send_messages=False))
                    members.handle_new_chat_members(update, context)
        except DBUser.DoesNotExist:
            found = False
            for member in context.bot.get_chat_administrators(chat.id):
                if member.user.id == sender.id:
                    found = True
            if not found:
                context.bot.restrict_chat_member(chat.id, sender.id, ChatPermissions(can_send_messages=False))
                members.handle_new_chat_members(update, context)

    utils.save_user(sender, chat)

import telegram
from telegram import Update, User, Message, Chat
from telegram.ext import CallbackContext, DispatcherHandlerStop
from django.conf import settings

from telegrambot import logging
from telegrambot.handlers import utils
from telegrambot.models import (
    Group as DBGroup,
    User as DBUser,
)


def handle_group_messages(update: Update, context: CallbackContext) -> None:
    """Handle a message in a group by updating the database.

    :raises: DispatcherHandlerStop if the messages comes from the bot itself or
    the group does not exists in the database.
    """
    message: Message = update.message or update.edited_message
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
        # TODO: re-enable this line
        # context.bot.leave_chat(chat_id=chat.id)
        raise DispatcherHandlerStop

    utils.save_user(sender, chat)


def handle_admin_tagging(update: Update, context: CallbackContext) -> None:
    """Handles the notifying of admins when @admin mention is used"""
    message: Message = update.message or update.edited_message
    sender: User = message.from_user
    chat: Chat = message.chat

    if sender.id == context.bot.id:
        raise DispatcherHandlerStop

    targets = message.parse_entities()
    found = False
    for target in targets:
        if targets[target][1:] == "admin":
            found = True
    if not found:
        raise DispatcherHandlerStop

    try:
        dbgroup = DBGroup.objects.get(id=chat.id)
    except DBGroup.DoesNotExist:
        # The group is not in the database; ignore all updates from it
        logging.log(logging.CHAT_DOES_NOT_EXIST, chat)
        # TODO: re-enable this line
        # context.bot.leave_chat(chat_id=chat.id)
        raise DispatcherHandlerStop

    try:
        dbuser = DBUser.objects.get(id=sender.id)
    except DBUser.DoesNotExist:
        dbuser = utils.save_user(sender, chat)

    caption = utils.generate_admin_tagging_notification(dbuser, dbgroup)
    context.bot.send_message(settings.TELEGRAM_ADMIN_GROUP_ID, caption, parse_mode="html", disable_web_page_preview=True)

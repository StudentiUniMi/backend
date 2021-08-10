from telegram import Update, User, Message, Chat
from telegram.ext import CallbackContext, DispatcherHandlerStop

from telegrambot.handlers import utils
from telegrambot.models import (
    Group as DBGroup,
)


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
        # TODO: Log this thing somewhere
        raise DispatcherHandlerStop

    utils.save_user(sender, chat)

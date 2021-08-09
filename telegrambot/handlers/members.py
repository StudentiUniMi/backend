from typing import List

from telegram import Update, User, Message, Chat
from telegram.ext import CallbackContext

from telegrambot.handlers import utils
from telegrambot.models import (
    User as DBUser,
    Group as DBGroup,
)


def handle_new_chat_members(update: Update, context: CallbackContext) -> None:
    """
    Handles new chat members who just joined a group
    """
    message: Message = update.message
    chat: Chat = message.chat
    members: List[User] = message.new_chat_members

    for member in members:
        if member.id == message.from_user.id:
            continue
        dbuser: DBUser = utils.save_user(member, chat, context.bot)
        utils.set_admin_rights(dbuser, chat)

    dbgroup: DBGroup = DBGroup.objects.get(id=chat.id)

    context.bot.send_message(
        chat_id=chat.id,
        text=dbgroup.generate_welcome_message(members),
        reply_to_message_id=message.message_id,
        parse_mode="html",
    )

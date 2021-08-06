from typing import List

from telegram import Update, User, Message, Chat
from telegram.ext import CallbackContext

from telegrambot.handlers import utils


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
        utils.save_user(member, chat, context.bot)

    welcome = f"{'Benvenuto' if len(members) == 1 else 'Benvenuti'} " \
              f"{', '.join([m.first_name for m in members])}"

    # TODO: per-group welcome message
    text = f"<b>{welcome}</b> nel gruppo \"{chat.title}\"!" \
           f"\n\nIscriviti al canale @studenti_unimi"

    context.bot.send_message(
        chat_id=chat.id,
        text=text,
        reply_to_message_id=message.message_id,
        parse_mode="html",
    )

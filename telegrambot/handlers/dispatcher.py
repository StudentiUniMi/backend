import telegram
import telegram.ext
from telegram import Update
from telegram.ext import MessageHandler, Filters
from telegram.ext.dispatcher import Dispatcher

from telegrambot.handlers import messages, members
from telegrambot.handlers.filters import NewChatMemberFilter


def dispatch_telegram_update(json_update: dict, token: str) -> None:
    bot = telegram.Bot(token=token)
    dispatcher = Dispatcher(bot, None, workers=0)

    # Pre-processing
    dispatcher.add_handler(MessageHandler(
        filters=Filters.chat_type.groups,
        callback=messages.handle_group_messages,
    ), group=0)

    # Groups
    dispatcher.add_handler(MessageHandler(
        filters=NewChatMemberFilter(),
        callback=members.handle_new_chat_members,
    ), group=1)

    update = Update.de_json(json_update, bot)
    dispatcher.process_update(update)

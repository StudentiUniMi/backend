import telegram
import telegram.ext
from telegram import Update
from telegram.ext import MessageHandler, Filters

from telegrambot.handlers import messages


def dispatch_telegram_update(json_update: dict, token: str) -> None:
    bot = telegram.Bot(token=token)
    dispatcher = telegram.ext.dispatcher.Dispatcher(bot, None, workers=0)
    dispatcher.add_handler(MessageHandler(
        filters=Filters.chat_type.groups,
        callback=messages.group_messages_handler,
    ))

    update = Update.de_json(json_update, bot)
    dispatcher.process_update(update)

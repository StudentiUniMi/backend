from django.conf import settings
from telegram import Update, TelegramError
from telegram.ext import CallbackContext

from telegrambot import logging


def telegram_error_handler(update: Update, context: CallbackContext) -> None:
    error = context.error
    if not isinstance(error, TelegramError):
        if settings.DEBUG:
            raise error
        return

    if update.effective_chat:
        logging.log(logging.TELEGRAM_ERROR, update.effective_chat, error_message=error.message)

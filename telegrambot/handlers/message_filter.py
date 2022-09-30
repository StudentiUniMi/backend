import re

from telegram import Update
from telegram.error import RetryAfter
from telegram.ext import CallbackContext

from telegrambot.models import MessageFilter
from telegrambot import tasks


def handle_message_filter(update: Update, context: CallbackContext):
    filters = MessageFilter.objects.all()
    filters = [re.compile(filt.text, re.IGNORECASE) for filt in filters]
    for filt in filters:
        if filt.fullmatch(update.message.text):
            try:
                update.message.delete()
            except RetryAfter:
                tasks.delete_message(update.message.chat.id, update.message.message_id)

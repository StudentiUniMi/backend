import re
import copy

from telegram import Update
from telegram.error import RetryAfter
from telegram.ext import CallbackContext

from telegrambot.models import MessageFilter
from telegrambot import tasks
from telegrambot.handlers.messages import handle_admin_tagging


class FakeUpdate:
    message = None


class FakeMessage:
    from_user = None
    chat = None
    reply_to_message = None


def handle_message_filter(update: Update, context: CallbackContext):
    filters = MessageFilter.objects.all()
    for filt in filters:
        f_regex = re.compile(filt.text, re.IGNORECASE)
        if f_regex.fullmatch(update.message.text):
            if filt.delete:
                try:
                    update.message.delete()
                except RetryAfter:
                    tasks.delete_message(update.message.chat.id, update.message.message_id)

            if filt.notify:
                # Create fake update obj
                new_update = FakeUpdate()
                new_update.message = copy.copy(update.message)
                new_update.message.text = "@admin"
                new_update.message.reply_to_message = update.message
                handle_admin_tagging(new_update, context)

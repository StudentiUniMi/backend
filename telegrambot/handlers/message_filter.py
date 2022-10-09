import re
import copy

from telegram import Update, ChatMemberOwner
from telegram.error import RetryAfter, TelegramError
from telegram.ext import CallbackContext

from telegrambot.models import MessageFilter
from telegrambot import tasks
from telegrambot.handlers.messages import handle_admin_tagging
from telegrambot.handlers.moderation import handle_moderation_command


ENUM_MODERATION = ["/warn", "/kick", "/ban", "/mute", "/free", "/superban", "/superfree"]


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
            if filt.notify:
                # Create fake update obj
                new_update = FakeUpdate()
                new_update.message = copy.copy(update.message)
                new_update.message.text = "@admin"
                new_update.message.message_id = -1
                new_update.message.reply_to_message = update.message
                handle_admin_tagging(new_update, context)

            if filt.reply:
                update.message.chat.send_message(filt.message, parse_mode="html", disable_web_page_preview=True)

            owner = None
            for adminis in update.message.chat.get_administrators():
                if isinstance(adminis, ChatMemberOwner):
                    owner = adminis.user

            if owner is not None:
                new_update = FakeUpdate()
                new_update.message = copy.copy(update.message)
                new_update.message.reply_to_message = update.message
                new_update.message.from_user = owner
                new_update.message.text = ENUM_MODERATION[filt.moderation - 3]
                handle_moderation_command(new_update, context)

            if filt.delete:
                try:
                    update.message.delete()
                except RetryAfter:
                    tasks.delete_message(update.message.chat.id, update.message.message_id)
                except TelegramError:
                    pass

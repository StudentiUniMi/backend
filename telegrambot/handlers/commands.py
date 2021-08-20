from telegram import Update, ChatPermissions
from telegram.ext import CallbackContext

from telegrambot.models import User, GroupMembership
from telegrambot.handlers import utils


def handle_force_verification(update: Update, context: CallbackContext) -> None:
    try:
        dbuser: User = User.objects.get(id=update.message.from_user.id)
        dbuser.verified = True
        dbuser.save()
        groups: list[GroupMembership] = GroupMembership.objects.filter(user_id=dbuser.id)
        for group in groups:
            context.bot.restrict_chat_member(group.group.id, dbuser.id, ChatPermissions(can_send_messages=True))
    except User.DoesNotExist:
        utils.save_user(update.message.from_user, None)

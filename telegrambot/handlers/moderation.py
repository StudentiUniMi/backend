from datetime import datetime, timedelta

import pytz
from django.conf import settings
from pytimeparse import timeparse
from telegram import Update, Message, User, Chat, ChatPermissions
from telegram.ext import CallbackContext

from telegrambot import tasks, logging
from telegrambot.handlers import utils


def handle_warn_command(update: Update, context: CallbackContext) -> None:
    """Handle a warn command, issued by an administrator."""
    message: Message = update.message
    sender: User = message.from_user
    chat: Chat = message.chat

    if not utils.can_moderate(sender, chat):
        return

    targets = utils.get_targets_of_command(message)
    if not targets:
        return

    text = "🟡 <b>I seguenti utenti sono stati warnati</b>:"
    for dbuser in targets:
        dbuser.warn_count += 1
        dbuser.save()
        warn_count = dbuser.warn_count
        text += f"\n- {dbuser.generate_mention()} [{warn_count}{' ⚠' if warn_count >= 3 else ''}]"
        logging.log(logging.MODERATION_WARN, chat=chat, target=dbuser, issuer=sender)

    msg = context.bot.send_message(chat_id=chat.id, text=text, parse_mode="html")
    tasks.delete_message(chat.id, msg.id)


def handle_kick_command(update: Update, context: CallbackContext) -> None:
    """Handle a kick command, issued by an administrator."""
    message: Message = update.message
    sender: User = message.from_user
    chat: Chat = message.chat

    if not utils.can_moderate(sender, chat):
        return

    targets = utils.get_targets_of_command(message)
    if not targets:
        return

    text = "⚪️ <b>I seguenti utenti sono stati kickati</b>:"
    for dbuser in targets:
        context.bot.unban_chat_member(chat_id=chat.id, user_id=dbuser.id)
        text += f"\n- {dbuser.generate_mention()}"
        logging.log(logging.MODERATION_KICK, chat=chat, target=dbuser, issuer=sender)

    msg: Message = context.bot.send_message(chat_id=chat.id, text=text, parse_mode="html")
    tasks.delete_message(chat.id, msg.message_id)


def handle_ban_command(update: Update, context: CallbackContext) -> None:
    """Handle a ban command, issued by an administrator."""
    message: Message = update.message
    sender: User = message.from_user
    chat: Chat = message.chat

    if not utils.can_moderate(sender, chat):
        return

    targets = utils.get_targets_of_command(message)
    if not targets:
        return

    text = "🔴️ <b>I seguenti utenti sono stati bannati dal gruppo</b>:"
    for dbuser in targets:
        context.bot.ban_chat_member(chat_id=chat.id, user_id=dbuser.id)
        text += f"\n- {dbuser.generate_mention()}"
        logging.log(logging.MODERATION_BAN, chat=chat, target=dbuser, issuer=sender)

    msg: Message = context.bot.send_message(chat_id=chat.id, text=text, parse_mode="html")
    tasks.delete_message(chat.id, msg.message_id)


def handle_mute_command(update: Update, context: CallbackContext) -> None:
    """Handle a mute command, issued by an administrator."""
    message: Message = update.message
    sender: User = message.from_user
    chat: Chat = message.chat

    if not utils.can_moderate(sender, chat):
        return

    targets = utils.get_targets_of_command(message)
    if not targets:
        return

    timestring = message.text.split(' ')[-1]
    duration = timeparse.timeparse(timestring)
    until_date = datetime.now(tz=pytz.timezone(settings.TIME_ZONE)) + timedelta(seconds=duration if duration else 0)

    text = f"🟠 <b>I seguenti utenti sono stati mutati dal gruppo</b>:"
    if duration:
        text = text[:-1] + f", fino al {until_date.strftime('%d/%m/%Y alle ore %H:%M:%S')}:"

    for dbuser in targets:
        context.bot.restrict_chat_member(
            chat_id=chat.id,
            user_id=dbuser.id,
            until_date=until_date,
            permissions=ChatPermissions(can_send_messages=False),
        )
        text += f"\n- {dbuser.generate_mention()}"
        logging.log(logging.MODERATION_MUTE, chat=chat, target=dbuser, issuer=sender,
                    until_date=until_date if duration else None)

    msg: Message = context.bot.send_message(chat_id=chat.id, text=text, parse_mode="html")
    tasks.delete_message(chat.id, msg.message_id)


def handle_free_command(update: Update, context: CallbackContext) -> None:
    """Handle a free command, issued by an administrator."""
    message: Message = update.message
    sender: User = message.from_user
    chat: Chat = message.chat

    if not utils.can_moderate(sender, chat):
        return

    targets = utils.get_targets_of_command(message)
    if not targets:
        return

    text = f"🟢 <b>I seguenti utenti sono stati liberati dalle restrizioni</b>:"
    for dbuser in targets:
        context.bot.unban_chat_member(
            chat_id=chat.id,
            user_id=dbuser.id,
            only_if_banned=True,
        )
        context.bot.restrict_chat_member(
            chat_id=chat.id,
            user_id=dbuser.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=True,
                can_invite_users=True,
                can_pin_messages=True,
            ),
        )
        text += f"\n- {dbuser.generate_mention()}"
        logging.log(logging.MODERATION_FREE, chat=chat, target=dbuser, issuer=sender)

    msg: Message = context.bot.send_message(chat_id=chat.id, text=text, parse_mode="html")
    tasks.delete_message(chat.id, msg.message_id)

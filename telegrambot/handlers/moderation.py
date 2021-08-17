from datetime import datetime, timedelta

import pytz
from django.conf import settings
from pytimeparse import timeparse
from telegram import Update, Message, User, Chat, ChatPermissions
from telegram.ext import CallbackContext

from telegrambot import tasks, logging
from telegrambot.handlers import utils
import telegrambot.models as t_models
import university.models as u_models


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


def handle_info_command(update: Update, context: CallbackContext) -> None:
    """Handles the info command issued by an administrator.

    The command is supposed to show information about the specified user(s).
    """
    # TODO
    message: Message = update.message
    sender: User = message.from_user
    chat: Chat = message.chat

    if not utils.can_moderate(sender, chat):
        return

    targets = utils.get_targets_of_command(message)
    if not targets:
        sender.send_message("Target(s) were not specified for comand `/info`!", parse_mode="markdown")
        return

    for dbuser in targets:
        text = ""
        user = t_models.User.objects.get(id=dbuser.id)
        text += "[" + str(user.id) + "](tg://user?id=" + str(user.id) + ")\n"
        text += ("Nome: " + user.first_name + "\n") if user.first_name is not None else ""
        text += ("Cognome: " + user.last_name + "\n") if user.last_name is not None else ""
        text += ("Username: " + user.username + "\n") if user.username is not None else ""
        text += "🔺 Reputazione: " + str(user.reputation) + "\n"
        text += "🟡 Ammonizioni: " + str(user.warn_count) + "\n"
        text += "🚫 E' bannato dal network? " + ("Si" if user.banned else "No") + "\n"
        text += "Livello dei permessi: " + str(user.permissions_level) + "\n"
        text += "🕗 Ultimo messaggio: " + str(user.last_seen.strftime("%d-%m-%Y %H:%M")) + "\n"

        privs = t_models.UserPrivilege.objects.filter(user=user.id)
        if privs is not None:
            text += "\n"
            for priv in privs:
                p_type = None
                for x in priv.PrivilegeTypes.choices:
                    if x[0] == priv.type:
                        p_type = x[1]
                if p_type is None:
                    continue

                text += "E' " + p_type

                if priv.scope == priv.PrivilegeScopes.GROUPS:
                    text += " nei seguenti gruppi:\n"
                    for group in t_models.Group.objects.filter(privileged_users__user__id=user.id):
                        text += "    \[`" + str(group.id) + "`] " + group.title + "\n"
                elif priv.scope == priv.PrivilegeScopes.DEGREES:
                    text += " nei gruppi dei seguenti C.d.L.:\n"
                    for degree in u_models.Degree.objects.filter(privileged_users__user_id=user.id):
                        text += "    " + degree.name + "\n"
                elif priv.scope == priv.PrivilegeScopes.DEPARTMENTS:
                    text += " nei gruppi dei seguenti dipartimenti:\n"
                    for department in u_models.Department.objects.filter(privileged_users__user_id=user.id):
                        text += "    " + department.name + "\n"
                else:
                    text += "\n"

        present_in_groups = t_models.GroupMembership.objects.filter(user__id=user.id)
        if present_in_groups is not None:
            text += "\nE' presente nei seguenti gruppi:\n"
            for group_mem in present_in_groups:
                if group_mem.group.invite_link is None or "":
                    text += "    \["+ str(group_mem.group.id) + "] " + group_mem.group.title + "\n"
                else:
                    text += "    \[[" + str(group_mem.group.id) +"](" + group_mem.group.invite_link + ")] "\
                            + group_mem.group.title + "\n"

    sender.send_message(text, parse_mode="markdown")

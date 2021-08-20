from datetime import datetime
from typing import List

from telegram import Update, User, Message, Chat, InlineKeyboardMarkup, InlineKeyboardButton, ChatMember,\
    ChatPermissions
from telegram.ext import CallbackContext

from telegrambot import tasks, logging
from telegrambot.handlers import utils
from telegrambot.models import (
    User as DBUser,
    Group as DBGroup,
    GroupMembership,
)


def handle_new_chat_members(update: Update, context: CallbackContext) -> None:
    """Handle new chat members who just joined a group and greet them"""
    message: Message = update.message
    chat: Chat = message.chat
    members: List[User] = message.new_chat_members

    for member in members:
        if member.id == message.from_user.id:
            continue
        dbuser: DBUser = utils.save_user(member, chat)
        utils.set_admin_rights(dbuser, chat)
        logging.log(logging.USER_JOINED, chat=chat, target=member)

    dbgroup: DBGroup = DBGroup.objects.get(id=chat.id)

    msg: Message = context.bot.send_message(
        chat_id=chat.id,
        text=dbgroup.generate_welcome_message(members),
        reply_to_message_id=message.message_id,
        parse_mode="html",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text="↗️ Visita studentiunimi.it",
                    url="https://studentiunimi.it/",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📣 Canale notizie",
                    url="https://t.me/studenti_unimi",
                ),
                InlineKeyboardButton(
                    text="👥 Gruppo generale",
                    url="https://t.me/unimichat",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✅",
                    callback_data="verify"
                )
            ],
        ]),
    )
    tasks.delete_message(chat.id, msg.message_id)


def handle_chat_member_updates(update: Update, _: CallbackContext) -> None:
    user: User = update.chat_member.from_user
    chat: Chat = update.chat_member.chat
    new: ChatMember = update.chat_member.new_chat_member

    GroupMembership.objects.update_or_create(
        user_id=new.user.id,
        group_id=chat.id,
        defaults={
            "status": new.status,
            "last_seen": datetime.now(),
        }
    )

    if new.status == ChatMember.LEFT:
        logging.log(logging.USER_LEFT, chat=chat, target=user)


def handle_verification(update: Update, context: CallbackContext) -> None:
    user = update.callback_query.from_user
    chat = update.callback_query.message.chat

    try:
        dbuser: DBUser = DBUser.objects.get(id=user.id)
        if not dbuser.verified:
            dbuser.verified = True
            dbuser.save()
            context.bot.restrict_chat_member(chat.id, user.id, ChatPermissions(can_send_messages=True))
    except DBUser.DoesNotExist:
        # If we don't find a user it means the user is already in the group, there's no need to register him here,
        # it will happen when he'll send the first message
        pass

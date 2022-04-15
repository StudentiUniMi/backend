from datetime import datetime

from telegram import Update, User, Message, Chat, InlineKeyboardMarkup, InlineKeyboardButton, ChatMember
from telegram.ext import CallbackContext

from telegrambot import tasks, logging
from telegrambot.handlers import utils
from telegrambot.models import (
    User as DBUser,
    Group as DBGroup,
    GroupMembership,
    BotWhitelist,
)


def handle_chat_member_updates(update: Update, context: CallbackContext) -> None:
    if not update.chat_member:
        # Ignore update.my_chat_member for now
        # TODO: Handle update.my_chat_member properly
        return

    user: User = update.chat_member.from_user
    chat: Chat = update.chat_member.chat
    old: ChatMember = update.chat_member.old_chat_member
    new: ChatMember = update.chat_member.new_chat_member

    utils.save_user(new.user, chat)

    if new.status == ChatMember.LEFT:
        logging.log(logging.USER_LEFT, chat=chat, target=user)

    if new.status == ChatMember.MEMBER:
        if old.status == ChatMember.ADMINISTRATOR:
            return

        if new.user.is_bot and not BotWhitelist.objects.filter(username=f"@{new.user.username}").exists():
            context.bot.kickChatMember(chat.id, new.user.id)
            return

        dbuser: DBUser = utils.save_user(new.user, chat)
        utils.set_admin_rights(dbuser, chat)
        logging.log(logging.USER_JOINED, chat=chat, target=new.user)

        dbgroup: DBGroup = DBGroup.objects.get(id=chat.id)

        # TODO: re-enable welcome messages
        if dbgroup.bot.username == "@studentiunimibot":
            return

        msg: Message = context.bot.send_message(
            chat_id=chat.id,
            text=dbgroup.generate_welcome_message([new.user, ]),
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
            ]),
        )
        tasks.delete_message(chat.id, msg.message_id)


def claim_command(update: Update, _: CallbackContext) -> None:
    """Claim admin privileges"""
    message = update.message
    user = message.from_user
    chat = message.chat
    dbuser = DBUser.objects.get(id=user.id)

    utils.set_admin_rights(dbuser, chat)
    message.delete()


def handle_left_chat_member_updates(update: Update, _: CallbackContext):
    """Delete 'user has left' and 'user has joined' services messages"""
    message: Message = update.message
    chat: Chat = message.chat
    if not message:
        return

    # Delete the "user joined" message if the group has more of 50 members
    if message.new_chat_members and chat.get_member_count() >= 50:
        tasks.delete_message(chat.id, message.message_id)

    if message.left_chat_member:
        update.message.delete()

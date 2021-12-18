from datetime import datetime
import logging as logg

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
    new: ChatMember = update.chat_member.new_chat_member

    utils.save_user(new.user, chat)
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
        update.message.delete()

    if new.status == ChatMember.MEMBER:
        if not new.user.is_bot:
            dbuser: DBUser = utils.save_user(new.user, chat)
            utils.set_admin_rights(dbuser, chat)
            logging.log(logging.USER_JOINED, chat=chat, target=new.user)
        else:
            whitelisted = BotWhitelist.objects.filter(username=f"@{new.user.username}")
            if len(whitelisted) == 0:
                context.bot.kickChatMember(chat.id, new.user.id)
                return

        dbgroup: DBGroup = DBGroup.objects.get(id=chat.id)

        # TODO: re-enable welcome messages
        if dbgroup.bot.username == "@studentiunimibot":
            return


def claim_command(update: Update, _: CallbackContext) -> None:
    """Claim admin privileges"""
    message = update.message
    user = message.from_user
    chat = message.chat
    dbuser = DBUser.objects.get(id=user.id)

    utils.set_admin_rights(dbuser, chat)
    message.delete()


def handle_left_chat_member_updates(update: Update, _: CallbackContext):
    """Delete 'user has left the group' status messages"""
    if not update.message or not update.message.left_chat_member:
        return
    update.message.delete()


def handle_join_request(update: Update, context: CallbackContext):
    """Sends the user info like rules of the channel and e markup keyboard with an accept rules button"""
    join_request = update.chat_join_request
    sender = join_request.from_user
    chat = join_request.chat

    group = DBGroup.objects.get(id=chat.id)

    sender.send_message(
        text=group.generate_welcome_message([sender, ]),
        parse_mode="html",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text="↗️ Visita studentiunimi.it",
                    url="https://studentiunimi.it/",
                ),
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
                    text="Accetto le regole ✔️",
                    callback_data=f"join_chat={chat.id}",
                )
            ],
        ]),
    )


def handle_join_approval(update: Update, context: CallbackContext):
    callback_query = update.callback_query
    chat = callback_query.data.split("=")[1]
    callback_query.from_user.approve_join_request(chat)
    callback_query.message.edit_reply_markup(InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text="↗️ Visita studentiunimi.it",
                url="https://studentiunimi.it/",
            ),
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
    ]))

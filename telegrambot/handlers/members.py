from datetime import datetime

from telegram import Update, User, Message, Chat, InlineKeyboardMarkup, InlineKeyboardButton, ChatMember,\
    ChatPermissions
from telegram.ext import CallbackContext, DispatcherHandlerStop

from telegrambot import tasks, logging
from telegrambot.handlers import utils
from telegrambot.models import (
    User as DBUser,
    Group as DBGroup,
    GroupMembership,
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

    if new.status == ChatMember.MEMBER:
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
                [
                    InlineKeyboardButton(
                        text="✅",
                        callback_data="verify"
                    )
                ],
            ]),
        )
        for member in members:
          dbuser: DBUser = DBUser.objects.get(id=member.id)
          if not dbuser.verified:
              context.bot.restrict_chat_member(chat.id, member.id, ChatPermissions(can_send_messages=False))
        tasks.delete_message(chat.id, msg.message_id)


def handle_verification(update: Update, context: CallbackContext) -> None:
    user = update.callback_query.from_user

    try:
        dbuser: DBUser = DBUser.objects.get(id=user.id)
        groups: list[GroupMembership] = GroupMembership.objects.filter(user_id=user.id)
        if not dbuser.verified:
            dbuser.verified = True
            dbuser.save()
            for group in groups:
                context.bot.restrict_chat_member(group.group.id, user.id, ChatPermissions(can_send_messages=True))
        else:
            for group in groups:
                context.bot.restrict_chat_member(group.group.id, user.id, ChatPermissions(can_send_messages=True))
    except DBUser.DoesNotExist:
        # If we don't find a user it means the user is already in the group, there's no need to register him here,
        # it will happen when he'll send the first message
        pass


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

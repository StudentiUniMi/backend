import logging as logg

from telegram import Update, User, Message, Chat, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, DispatcherHandlerStop
from django.conf import settings
from django.db.models import Q, Count

from telegrambot import logging
from telegrambot.handlers import utils
from telegrambot.models import (
    Group as DBGroup,
    User as DBUser,
    UserPrivilege,
)
from university.models import Degree


LOG = logg.getLogger(__name__)


def handle_group_messages(update: Update, context: CallbackContext) -> None:
    """Handle a message in a group by updating the database.

    :raises: DispatcherHandlerStop if the messages comes from the bot itself or
    the group does not exists in the database.
    """
    message: Message = update.message or update.edited_message
    sender: User = message.from_user
    chat: Chat = message.chat

    if sender.id == context.bot.id:
        # Ignore messages sent by the bot itself
        raise DispatcherHandlerStop

    try:
        dbgroup = DBGroup.objects.get(id=chat.id)
        dbgroup.title = chat.title
        dbgroup.save(force_update=True, update_fields=["title", ])
    except DBGroup.DoesNotExist:
        # The group is not in the database; ignore all updates from it
        logging.log(logging.CHAT_DOES_NOT_EXIST, chat)
        # TODO: re-enable this line
        # context.bot.leave_chat(chat_id=chat.id)
        raise DispatcherHandlerStop

    utils.save_user(sender, chat)


def handle_admin_tagging(update: Update, context: CallbackContext) -> None:
    """Handles the notifying of admins when @admin mention is used"""
    message: Message = update.message or update.edited_message
    sender: User = message.from_user
    chat: Chat = message.chat
    reply_to: Message = message.reply_to_message

    if sender.id == context.bot.id:
        raise DispatcherHandlerStop

    targets = message.parse_entities()
    if not any([targets[target][1:] == "admin" for target in targets]):
        return

    dbgroup = DBGroup.objects.filter(id=chat.id)
    if len(dbgroup) == 0:
        return
    dbgroup = dbgroup[0]
    if dbgroup.ignore_admin_tagging:
        return

    try:
        dbuser = DBUser.objects.get(id=sender.id)
    except DBUser.DoesNotExist:
        dbuser = utils.save_user(sender, chat)
    if reply_to is not None:
        try:
            dbtarget = DBUser.objects.get(id=reply_to.from_user.id)
        except DBUser.DoesNotExist:
            dbtarget = utils.save_user(reply_to.from_user, chat)
    else:
        dbtarget = None

    # Get privs
    degrees = [
        *Degree.objects.filter(courses__group__id=chat.id),
        *Degree.objects.filter(group__id=chat.id)
    ]
    privs = UserPrivilege.objects.filter(
        Q(scope=UserPrivilege.PrivilegeScopes.DEGREES, authorized_degrees__in=degrees) |
        Q(scope=UserPrivilege.PrivilegeScopes.GROUPS, authorized_groups__id=chat.id) |
        Q(scope=UserPrivilege.PrivilegeScopes.DEPARTMENTS, authorized_departments__degrees__in=degrees) |
        Q(scope=UserPrivilege.PrivilegeScopes.ALL)
    ).filter(type=UserPrivilege.PrivilegeTypes.ADMIN).annotate(u_count=Count("user"))  # Gets only users with type "Amministratore"
    LOG.info(privs)

    logging.log(logging.USER_CALLED_ADMIN, chat, target=dbtarget, issuer=dbuser, msg=reply_to)

    caption = utils.generate_admin_tagging_notification(dbuser, dbgroup, privs, reply_to)
    context.bot.send_message(settings.TELEGRAM_ADMIN_GROUP_ID, caption, parse_mode="html", disable_web_page_preview=True)


def request_broadcast_message(update: Update, context: CallbackContext):
    """Command handler for /broadcast used to broadcast a message to all groups of the network"""
    message = update.message
    issuer = update.message.from_user

    if not utils.can_superban(issuer):
        return

    issuer.send_message(
        message.text_markdown_v2[11:],
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text="Send",
                    callback_data="broadcast_send"
                ),
                InlineKeyboardButton(
                    text="❌",
                    callback_data="broadcast_discard"
                )
            ]
        ]),
        parse_mode="markdown"
    )
    message.delete()


def handle_broadcast_confirm(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.callback_query.message

    message.edit_text(message.text_markdown_v2)

    for group in DBGroup.objects.all():
        bot.send_message(group.id, message.text_markdown_v2, parse_mode="markdown")

    logging.log(logging.BROADCAST, None, issuer=update.callback_query.from_user, msg=message)
    message.delete()


def handle_broadcast_discard(update: Update, context: CallbackContext):
    update.callback_query.message.delete()

import logging as logg
import telegram
from polymorphic.query import PolymorphicQuerySet

from django.utils.translation import gettext_lazy as _

from telegram import Update, User, Message, Chat, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, DispatcherHandlerStop
from django.conf import settings
from django.db.models import Q, QuerySet

from roles.models import Moderator, SuperAdministrator, Administrator, BaseRole
from telegrambot import logging, tasks
from telegrambot.handlers import utils
from telegrambot.models import (
    Group as DBGroup,
    User as DBUser,
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

    utils.save_user(sender, chat, count_message=True)


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

    logging.log(logging.USER_CALLED_ADMIN, chat, target=dbtarget, issuer=dbuser, msg=reply_to)

    # Get users with privileges (>= Moderator) on the group
    degrees: QuerySet[Degree] = Degree.objects.filter(
        Q(courses__group__id=chat.id) | Q(group__id=chat.id)
    )
    if degrees:
        roles: PolymorphicQuerySet[BaseRole] = BaseRole.objects.filter(
            Q(degrees__in=degrees) | Q(all_groups=True)
        )
    else:
        roles: PolymorphicQuerySet[BaseRole] = BaseRole.objects.filter(extra_groups=True)
    roles = roles.instance_of(Moderator) | roles.instance_of(Administrator) | roles.instance_of(SuperAdministrator)

    caption = utils.generate_admin_tagging_notification(dbuser, dbgroup, roles, reply_to)
    context.bot.send_message(
        settings.TELEGRAM_ADMIN_GROUP_ID,
        caption,
        parse_mode="html",
        disable_web_page_preview=True,
    )

    utils.activate_group_language(dbgroup, dbuser)
    sent_msg: Message = context.bot.send_message(
        chat.id,
        str(_("👮 <b>Thanks for your report</b>, admins have been notified.")),
        parse_mode="html",
        disable_web_page_preview=True,
    )
    context.bot.delete_message(chat.id, message.message_id)
    tasks.delete_message(chat.id, sent_msg.message_id)


def request_broadcast_message(update: Update, _: CallbackContext):
    """Command handler for /broadcast used to broadcast a message to all groups of the network"""
    message = update.message
    issuer = update.message.from_user

    if not utils.is_superadmin(issuer):
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
    issuer = update.callback_query.from_user

    if not utils.is_superadmin(issuer):
        return

    message.edit_text(message.text_markdown_v2)

    for group in DBGroup.objects.all():
        try:
            bot.send_message(group.id, message.text_markdown_v2, parse_mode="markdown")
        except telegram.TelegramError:
            continue

    logging.log(logging.BROADCAST, None, issuer=issuer, msg=message)
    message.delete()


def handle_broadcast_discard(update: Update, _: CallbackContext):
    issuer = update.callback_query.from_user

    if not utils.is_superadmin(issuer):
        return

    update.callback_query.message.delete()

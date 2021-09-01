from datetime import datetime

import telegram
from django.apps import apps
from django.conf import settings
from django.urls import reverse
from telegram import User, Chat, TelegramError
from telegram.ext import DispatcherHandlerStop
from telegram.utils.helpers import escape

import telegrambot.models as t_models
import university.models as u_models
from telegrambot import logging


# def get_bot(chat: Union[Chat, telegrambot.Group, int]) -> telegram.Bot
def get_bot(chat: Chat) -> telegram.Bot:
    """Get the proper telegram.Bot instance for a chat.

    :param chat: the considered Telegram chat
    :return: the telegram.Bot who is in that chat
    """
    DBGroup = apps.get_model("telegrambot.Group")
    if isinstance(chat, DBGroup):
        dbgroup = chat
    else:
        dbgroup = DBGroup.objects.get(id=chat if isinstance(chat, int) else chat.id)
    bot = telegram.Bot(dbgroup.bot.token)
    return bot


# Annotations in this file are not always possible because circular imports
# def save_user(user: User, chat: Chat) -> telegrambot.User
def save_user(user: User, chat: Chat):
    """Save a Telegram user and their group membership to the database.
    Should be used before processing any update, to ensure the correctness of the database.
    If the user is globally banned, it will be banned from the chat.

    :param user: the Telegram user to save
    :param chat: the Telegram chat the user is in
    :return: telegrambot.User object representing the user
    """
    DBUser = apps.get_model("telegrambot.User")
    dbuser = DBUser.objects.update_or_create(
        id=user.id,
        defaults={
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "last_seen": datetime.now(),
        }
    )[0]
    if dbuser.banned:
        # The user is globally banned from the network
        bot = get_bot(chat)
        bot.ban_chat_member(
            chat_id=chat.id,
            user_id=user.id,
        )
        raise DispatcherHandlerStop

    DBGroupMembership = apps.get_model("telegrambot.GroupMembership")
    dbmembership = DBGroupMembership.objects.update_or_create(
        user_id=user.id,
        group_id=chat.id,
        defaults={
            "last_seen": datetime.now(),
        }
    )[0]
    dbmembership.messages_count += 1
    dbmembership.save()
    return dbuser


# def set_admin_rights(dbuser: telegrambot.User, chat: Union[telegram.Chat, telegrambot.Chat]) -> None
def set_admin_rights(dbuser, chat) -> None:
    """Try to set chat admin rights in a chat if the user has privileges.

    :param dbuser: the telegrambot.User to promote
    :param chat: the considered Telegram chat
    :return: None
    """
    privileges = dbuser.get_privileges(chat)
    if not privileges:
        return

    bot = get_bot(chat)
    try:
        bot.promote_chat_member(
            chat_id=chat.id,
            user_id=dbuser.id,
            can_change_info=privileges.can_change_info,
            can_delete_messages=privileges.can_delete_messages,
            can_invite_users=privileges.can_invite_users,
            can_restrict_members=privileges.can_restrict_members,
            can_pin_messages=privileges.can_pin_messages,
            can_promote_members=privileges.can_promote_members,
            can_manage_chat=privileges.can_manage_chat,
            can_manage_voice_chats=privileges.can_manage_voice_chats,
        )
        bot.set_chat_administrator_custom_title(
            chat_id=chat.id,
            user_id=dbuser.id,
            custom_title=privileges.custom_title,
        )
    except TelegramError as e:
        if e.message == "Chat not found":
            logging.log(logging.CHAT_DOES_NOT_EXIST, chat=chat, target=bot)
        elif e.message == "Not enough rights":
            logging.log(logging.NOT_ENOUGH_RIGHTS, chat=chat, target=bot)


# def remove_admin_rights(dbuser: telegrambot.User, chat: Union[telegram.Chat, telegrambot.Chat]) -> None
def remove_admin_rights(dbuser, chat) -> None:
    """Remove all admin rights of an user in a chat.

    :param dbuser: the telegrambot.User to demote
    :param chat: the considered Telegram chat
    :return: None
    """
    bot = get_bot(chat)
    try:
        bot.promote_chat_member(
            chat_id=chat.id,
            user_id=dbuser.id,
            can_change_info=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False,
            can_manage_chat=False,
            can_manage_voice_chats=False,
        )
    except TelegramError:
        # The bot has no enough rights
        # TODO: Alert administrators
        pass


def can_moderate(user, chat) -> bool:
    """Return True if the user can restrict other members"""
    DBUser = apps.get_model("telegrambot.User")

    dbuser: DBUser = DBUser.objects.get(id=user.id)
    privileges = dbuser.get_privileges(chat)
    if not privileges or not privileges.can_restrict_members:
        return False
    return True


def can_superban(user) -> bool:
    """Return True if the user can superban other members"""
    Privileges = apps.get_model("telegrambot.UserPrivilege")
    try:
        privs = Privileges.objects.get(user_id=user.id)
    except Privileges.DoesNotExist:
        return False
    return privs.can_superban_members


def get_targets_of_command(message):
    """Get the target users of a command."""
    DBUser = apps.get_model("telegrambot.User")

    entities = message.parse_entities()
    targets = list()
    for entity in entities:
        parsed = entities[entity]
        if entity.type == "mention":
            try:
                dbuser = DBUser.objects.get(username__iexact=parsed[1:])
                targets.append(dbuser)
            except DBUser.DoesNotExist or DBUser.MultipleObjectsReturned:
                continue
        elif entity.type == "text_mention":
            try:
                dbuser = DBUser.objects.get(id=entity.user.id)
                targets.append(dbuser)
            except DBUser.DoesNotExist:
                continue

    if message.reply_to_message:
        try:
            dbuser = DBUser.objects.get(id=message.reply_to_message.from_user.id)
            targets.append(dbuser)
        except DBUser.DoesNotExist:
            pass

    return targets


def get_admin_url(model):
    return settings.REAL_HOST + \
           reverse(f"admin:{model._meta.app_label}_{model._meta.model_name}_change", args=(model.pk, ))


def format_group_membership(dbmembership):
    group = dbmembership.group
    user = dbmembership.user

    text = f"[<code>{group.id}</code>|"
    text += f"<a href=\"{get_admin_url(group)}\">AG</a>|"
    text += f"<a href=\"{get_admin_url(user)}\">AU</a>|"
    text += f"<a href=\"{group.invite_link}\">L</a>|" if group.invite_link else ""
    text += f"{dbmembership.status[:3].upper()}"
    text += f"] {group.title}"
    return text


def format_user_info(dbuser):
    """Format some Telegram user information.

    Used by the /info command.
    """
    try:
        user = t_models.User.objects.get(id=dbuser.id)
    except t_models.User.DoesNotExist:
        return None

    text = f"👤 <b>Utente</b> <a href=\"tg://user?id={user.id}\">{escape(user.name)}</a>"
    text += f"\n🔖 <b>Username</b>: @{escape(user.username)}" if user.username else ""
    text += f"\n🔺 <b>Reputazione</b>: {user.reputation}"
    text += f"\n🟡 <b>Ammonizioni</b>: {user.warn_count}"
    text += f"\n👮‍ <b>Livello di permessi</b>: {user.permissions_level}"
    text += f"\n🕗 <b>Ultimo messaggio</b>: {user.last_seen.strftime('%d-%m-%Y %H:%M:%S')}"
    if user.banned:
        text += "\n⚫️ <b>Il membro è bannato globalmente dal network</b>."

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

            text += f"\n⭐ ️È <b>{p_type.lower()}</b> "
            if priv.can_restrict_members:
                text += "(<b>+</b>) "

            if priv.scope == priv.PrivilegeScopes.GROUPS:
                text += "nei seguenti gruppi:\n"
                for group in t_models.Group.objects.filter(privileged_users__user__id=user.id):
                    text += f"➖ [<code>{group.id}</code>] {escape(group.title)}\n"
            elif priv.scope == priv.PrivilegeScopes.DEGREES:
                text += "dei seguenti C.d.L.:\n"
                for degree in u_models.Degree.objects.filter(privileged_users__user_id=user.id):
                    text += f"➖ {escape(degree.name)}\n"
            elif priv.scope == priv.PrivilegeScopes.DEPARTMENTS:
                text += "dei seguenti dipartimenti:\n"
                for department in u_models.Department.objects.filter(privileged_users__user_id=user.id):
                    text += f"➖ {escape(department.name)}\n"
            else:
                text += "in tutto l'Ateneo\n"

    present_in_groups = t_models.GroupMembership.objects.filter(user__id=user.id).order_by("messages_count").reverse()
    if present_in_groups is None:
        return text

    text += "\n👥 <b>È stato visto nei seguenti gruppi</b>:\n"
    for dbmembership in present_in_groups:
        text += f"➖ {format_group_membership(dbmembership)}\n"

    return text

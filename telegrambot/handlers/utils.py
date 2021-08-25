from datetime import datetime

import telegram
from django.apps import apps
from telegram import User, Chat, TelegramError
from telegram.ext import DispatcherHandlerStop
import telegrambot.models as t_models
import university.models as u_models


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
    except TelegramError:
        # The bot has no enough rights
        # TODO: Alert administrators
        pass


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


def format_user_info(dbuser):
    """Format some Telegram user information.

    Used by the /info command.
    """
    try:
        user = t_models.User.objects.get(id=dbuser.id)
    except t_models.User.DoesNotExist:
        return None

    text = "👤 *Utente* [{name}](tg://user?id={id}) \[`{id}`]".format(name=user.name, id=user.id)
    text += ("\n🔖 *Username*: @" + user.username) if user.username is not None else ""
    text += "\n🔺 *Reputazione*: {}".format(user.reputation)
    text += "\n🟡 *Ammonizioni*: {}".format(user.warn_count)
    text += "\n👮‍️ *Livello dei permessi*: {}".format(user.permissions_level)
    text += "\n🕗 *Ultimo messaggio*: {}".format(user.last_seen.strftime("%d-%m-%Y %H:%M:%S"))
    if user.banned:
        text += "\n⚫️ *Il membro è bannato globalmente dal network*."

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

            text += "\n⭐ ️È *{}* ".format(p_type.lower())
            if priv.can_restrict_members:
                text += "(*moderatore*) "

            if priv.scope == priv.PrivilegeScopes.GROUPS:
                text += "nei seguenti gruppi:\n"
                for group in t_models.Group.objects.filter(privileged_users__user__id=user.id):
                    text += "➖ \[`" + str(group.id) + "`] " + group.title + "\n"
            elif priv.scope == priv.PrivilegeScopes.DEGREES:
                text += "dei seguenti C.d.L.:\n"
                for degree in u_models.Degree.objects.filter(privileged_users__user_id=user.id):
                    text += "➖ " + degree.name + "\n"
            elif priv.scope == priv.PrivilegeScopes.DEPARTMENTS:
                text += "dei seguenti dipartimenti:\n"
                for department in u_models.Department.objects.filter(privileged_users__user_id=user.id):
                    text += "➖ " + department.name + "\n"
            else:
                text += "\n"

    present_in_groups = t_models.GroupMembership.objects.filter(user__id=user.id).order_by("messages_count").reverse()
    if present_in_groups is None:
        return text

    text += "\n👥 *È stato visto nei seguenti gruppi*:\n"
    for group_mem in present_in_groups:
        if not group_mem.group.invite_link:
            text += "➖ *{}* \[`{}`]".format(group_mem.group.title, group_mem.group.id)
        else:
            text += "➖ *{}* \[[`{}`]({})]".format(group_mem.group.title, group_mem.group.id, group_mem.group.invite_link)
        text += " ({}), {} msg\n".format(group_mem.status.upper(), group_mem.messages_count)
    return text

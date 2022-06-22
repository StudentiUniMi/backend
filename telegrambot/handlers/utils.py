from datetime import datetime
import logging as logg

import telegram
from django.apps import apps
from django.conf import settings
from django.db.models import Q, QuerySet
from django.urls import reverse
from polymorphic.query import PolymorphicQuerySet
from telegram import User, Chat, TelegramError, Message
from telegram.ext import DispatcherHandlerStop
from telegram.utils.helpers import escape

import telegrambot.models as t_models
import university.models as u_models
from telegrambot import logging
from telegrambot.logging import EventTypes

LOG = logg.getLogger(__name__)


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


def check_blacklist(dbuser: t_models.User):
    """Check if a user is blacklisted or not.
    If the user is blacklisted, set its banned attribute to True and log the action
    in the logging system.

    :param dbuser: the user to check
    """
    if dbuser.banned:
        # the user is already banned or blacklisted
        return

    BlacklistedUser = t_models.BlacklistedUser
    try:
        blacklisted_user: BlacklistedUser = BlacklistedUser.objects.get(user_id=dbuser.id)
    except BlacklistedUser.DoesNotExist:
        return

    logging.log(
        event=logging.MODERATION_SUPERBAN,
        chat=None,
        target=dbuser,
        reason=f"the user is blacklisted (source: {blacklisted_user.get_source_display()})",
    )
    dbuser.banned = True
    dbuser.save()


# Annotations in this file are not always possible because circular imports
# def save_user(user: User, chat: Chat) -> telegrambot.User
def save_user(user: User, chat: Chat, count_message: bool = False):
    """Save a Telegram user and their group membership to the database.
    Should be used before processing any update, to ensure the correctness of the database.
    If the user is globally banned, it will be banned from the chat.

    :param user: the Telegram user to save
    :param chat: the Telegram chat the user is in
    :param count_message: whatever to increment messages_count to GroupMembership or not
    :return: telegrambot.User object representing the user
    """
    DBUser = apps.get_model("telegrambot.User")
    dbuser = DBUser.objects.update_or_create(
        id=user.id,
        defaults={
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "language": user.language_code,
            "last_seen": datetime.now(),
        }
    )[0]
    check_blacklist(dbuser)
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
    dbmembership.messages_count += 1 if count_message else 0
    dbmembership.save()
    return dbuser


# def set_admin_rights(dbuser: telegrambot.User, chat: Union[telegram.Chat, telegrambot.Chat]) -> None
def set_admin_rights(user, chat, force=False) -> None:
    """Try to set chat admin rights in a chat if the user has privileges.

    :param user: the telegrambot.User to promote
    :param chat: the considered Telegram chat
    :param force: force privileges setting (use this to remove privileges)
    :return: None
    """
    _, telegram_permissions, custom_title = get_permissions(user.id, chat.id)

    bot = get_bot(chat)
    try:
        if force or any([telegram_permissions[k] for k in telegram_permissions]):
            bot.promote_chat_member(
                chat_id=chat.id,
                user_id=user.id,
                **telegram_permissions,
            )
            if custom_title:
                bot.set_chat_administrator_custom_title(
                    chat_id=chat.id,
                    user_id=user.id,
                    custom_title=custom_title,
                )
    except TelegramError as e:
        if e.message == "Chat not found":
            logging.log(logging.CHAT_DOES_NOT_EXIST, chat=chat, target=bot)
        elif e.message == "Not enough rights":
            logging.log(logging.NOT_ENOUGH_RIGHTS, chat=chat, target=bot)


def get_permissions(user_id: int, chat_id: int) -> tuple[list[EventTypes | None], dict[str, bool], str | None]:
    BaseRole = apps.get_model("roles.BaseRole")
    group_degrees: QuerySet[u_models.Degree] = u_models.Degree.objects.filter(
        Q(courses__group_id=chat_id) | Q(group__id=chat_id)
    )
    roles: PolymorphicQuerySet[BaseRole] = BaseRole.objects.filter(tg_user=user_id)
    if group_degrees:
        roles = roles.filter(Q(degrees__in=group_degrees) | Q(all_groups=True))
    else:
        roles = roles.filter(extra_groups=True)

    permissions: list[EventTypes | None] = []
    telegram_permissions: dict[str, bool] = {}
    custom_title = None
    for role in roles:
        permissions.extend(role.permissions())
        telegram_permissions = {
            **telegram_permissions,
            **role.telegram_permissions(),
        }
        custom_title = role.custom_title()
    return permissions, telegram_permissions, custom_title


def is_superadmin(user) -> bool:
    """Return True if the user is a SuperAdministrator"""
    SuperAdministrator = apps.get_model("roles.SuperAdministrator")
    return SuperAdministrator.objects.filter(Q(tg_user=user.id) & Q(all_groups=True)).count() > 0


def get_targets_of_command(message: Message):
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

    # Target from IDs
    for p_target in message.text.split(" "):
        try:
            dbuser = DBUser.objects.get(id=p_target)
            targets.append(dbuser)
        except DBUser.DoesNotExist:
            pass
        except ValueError:
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
    result = []

    try:
        user = t_models.User.objects.get(id=dbuser.id)
    except t_models.User.DoesNotExist:
        return result

    text = f"👤 <b>Utente</b> <a href=\"tg://user?id={user.id}\">{escape(user.name)}</a> [{user.id}]"
    text += f"\n🔖 <b>Username</b>: @{escape(user.username)}" if user.username else ""
    text += f"\n🔺 <b>Reputazione</b>: {user.reputation}"
    text += f"\n🟡 <b>Ammonizioni</b>: {user.warn_count}"
    text += f"\n👮‍ <b>Livello di permessi</b>: {user.permissions_level}"
    text += f"\n🕗 <b>Ultimo messaggio</b>: {user.last_seen.strftime('%d-%m-%Y %H:%M:%S')}"
    if user.banned:
        text += "\n⚫️ <b>Il membro è bannato globalmente dal network</b>."

    present_in_groups = t_models.GroupMembership.objects.filter(user__id=user.id).order_by("messages_count").reverse()
    if present_in_groups is None:
        return result

    if len(text + "\n👥 <b>È stato visto nei seguenti gruppi</b>:\n") > 4096:
        result.append(text)
        text = ""
    text += "\n👥 <b>È stato visto nei seguenti gruppi</b>:\n"
    for dbmembership in present_in_groups:
        if len(text + f"{format_group_membership(dbmembership)}") > 4096:
            result.append(text)
            text = ""
        text += f"➖ {format_group_membership(dbmembership)}\n"

    result.append(text)
    return result


def generate_group_creation_message(group: telegram.Chat) -> str:
    dbgroup = t_models.Group.objects.get(id=group.id)
    dbdegree = u_models.Degree.objects.get(group_id=dbgroup.id)
    degree_type = ""
    for t in u_models.DEGREE_TYPES:
        if t[0] == dbdegree.type:
            degree_type = t[1]

    text = (
        "<a href=\"https://studentiunimi.it\">📣</a> <b>BENVENUTI, e buona permanenza</b>!"
        f"\n📍 Sei nel <b>gruppo</b> Telegram principale del CdL di {dbdegree.name} ({degree_type})."
        "\n👥 Puoi usare questo gruppo per <b>scaricare</b> e <b>condividere</b> materiali, "
        "<b>chiedere</b> informazioni o <b>conoscere</b> i tuoi compagni di corso."

        "\n\n🎉 Scopri il nostro <b>network StudentiUniMi</b>: stiamo creando e gestendo gruppi Telegram per ogni corso "
        "di laurea e insegnamento, in modo da facilitare la comunicazione tra gli studenti e la condivisione di "
        f"informazioni. A <a href=\"https://studentiunimi.it/courses/{dbdegree.slug}\">questo link</a> puoi trovare "
        "tutti i gruppi associati a questo corso di laurea."
        "\n🗣 <b>Condividi</b> i gruppi ai tuoi colleghi per liberarli dai "
        "fastidiosissimi gruppi WhatsApp ingestibili ;)"
        "\n😬 <b>Nessuno scrive</b>? All'inizio è normale un po' di imbarazzo: "
        "<i>sii il cambiamento che vuoi vedere nel mondo</i>."

        "\n\n🌍 <b>Gruppo principale degli studenti dell'Ateneo</b>: @unimichat"
        "\n🤘 <b>Server Discord</b>: https://discord.gg/SwPzAkv4A4"
        "\n💻 <b>Sito web</b> del network: https://studentiunimi.it"
        "\n📰 <b>Canale Telegram</b> del network: @studenti_unimi"
        "\n✅ <b>Alternativa ad UNIMIA</b>, sempre online: https://unimia.studentiunimi.it"
        "\n👮 <i>Cerchiamo amministratori e moderatori, se sei interessato/a contattaci!</i>"
    )
    return text


def generate_admin_tagging_notification(sender, chat, roles, reply_to: Message) -> str:
    admins = ""
    for admin in {role.tg_user for role in roles}:
        admins += f"{admin.generate_mention()} "
    name = sender.username if sender.username else sender.first_name
    text = f"A user has tagged @admin\n"\
           f"👤 <b>Issuer</b>: {escape(name)} [<a href=\"tg://user?id={sender.id}\">{sender.id}</a>]\n"\
           f"👥 <b>Group</b>: {escape(chat.title)} [<a href=\"{chat.invite_link}\">{chat.id}</a>]\n"\
           f"👮 <b>Please respond</b> {admins}"
    if reply_to is not None:
        text += f"\n<b>Target</b>: {escape(reply_to.from_user.name)} [<a href=\"tg://user?id={reply_to.from_user.id}\">{reply_to.from_user.id}</a>]"
        text += f"\n📜 <b>Message</b>: {reply_to.text}[<a href='https://t.me/c/1{str(reply_to.chat.id)[5:]}/{reply_to.message_id}'>{reply_to.message_id}</a>]"
    return text

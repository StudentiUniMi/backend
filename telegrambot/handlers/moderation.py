import logging as logg
from time import sleep

from telegram import Update, Message, User, Chat, ChatPermissions, MessageEntity, Bot
from telegram.ext import CallbackContext
from telegram.error import RetryAfter

from telegrambot import tasks, logging
from telegrambot.logging import EventTypes
from telegrambot.handlers import utils
from telegrambot.models import (
    Group as DBGroup,
    User as DBUser,
    BotWhitelist
)


LOG = logg.getLogger(__name__)


class NoTargetsInCommand(Exception):
    pass


class ModerationCommand:
    issuer: User
    target: DBUser
    event: logging.EventTypes
    reason: str | None
    target_message: Message | None

    def __init__(self, bot: Bot, message: Message):
        self.bot = bot
        self._message: Message = message
        self._text: str = message.text
        self._command: str = self._text.split()[0][1:].split("@")[0].lower()
        self.issuer: User = self._message.from_user
        self.event = self._match_command()
        self.target, self.reason = self._decode_args()
        self.target_message = self._message.reply_to_message

        if self.event == logging.EventTypes.MODERATION_DEL and not self.target_message:
            raise NoTargetsInCommand()

        if not self._check_permissions():
            raise PermissionError()

    @property
    def _chat_id(self):
        return self._message.chat.id

    def _match_command(self) -> EventTypes:
        for event_type in EventTypes:
            if event_type.command == self._command:
                return event_type
        raise ValueError(f"no handler for command /{self._command}")

    def _decode_args(self) -> tuple[DBUser, str | None]:
        """Get the target user of a command and a (optional) reason for the action

        Command specification:
        /command <target> [moderation message]
        OR
        (Replying to a message) /command [moderation message]

        target can ether be a @Username, a mention of a Telegram user ID
        """
        entities: dict[MessageEntity, str] = self._message.parse_entities(
            types=[MessageEntity.MENTION, MessageEntity.TEXT_MENTION],
        )

        reason: str | None = None
        if len(arguments := self._text.split()[1:]) > 0:
            reason = ' '.join(arguments)

            if len(entities) != 0:
                entity: tuple[MessageEntity, str] = entities.popitem()
                target: DBUser | None = None
                match entity[0].type:
                    # /command @Username [moderation message]
                    case MessageEntity.MENTION:
                        try:
                            target = DBUser.objects.get(username__iexact=entity[1][1:])
                        except (DBUser.DoesNotExist, DBUser.MultipleObjectsReturned):
                            pass

                    # /command Mention [moderation message]
                    case MessageEntity.TEXT_MENTION:
                        try:
                            target = DBUser.objects.get(id=entity[0].user.id)
                        except DBUser.DoesNotExist:
                            pass
                if target:
                    return target, ' '.join(reason.split()[1:]) if reason else None

            # /command USER_ID [moderation message]
            try:
                return DBUser.objects.get(id=int(self._text.split()[1])), \
                       ' '.join(reason.split()[1:]) if reason else None
            except (DBUser.DoesNotExist, ValueError):
                pass

        # (Replying to a message) /command [moderation message]
        if reply_to := self._message.reply_to_message:
            try:
                return DBUser.objects.get(id=reply_to.from_user.id), reason
            except DBUser.DoesNotExist:
                pass

        raise NoTargetsInCommand()

    def _check_permissions(self) -> bool:
        permissions, _, __ = utils.get_permissions(self.issuer.id, self._chat_id)
        return self.event in permissions

    def dispatch(self):
        match self.event:
            case EventTypes.MODERATION_INFO:
                self.info()

            case EventTypes.MODERATION_DEL:
                self.delete()

            case EventTypes.MODERATION_WARN:
                self.warn()

            case EventTypes.MODERATION_KICK:
                self.kick()

            case EventTypes.MODERATION_MUTE:
                self.mute()

            case EventTypes.MODERATION_BAN:
                self.ban()

            case EventTypes.MODERATION_FREE:
                self.free()

            case EventTypes.MODERATION_SUPERBAN:
                self.superban()

            case EventTypes.MODERATION_SUPERFREE:
                self.superfree()

    def info(self):
        texts = utils.format_user_info(self.target)

        # User must start the bot in private before he can receive messages from it
        for text in texts:
            while True:
                try:
                    self.issuer.send_message(text, parse_mode="html", disable_web_page_preview=True)
                    break
                except RetryAfter as e:
                    sleep(e.retry_after)

    def delete(self):
        self.target_message.delete()

    def warn(self):
        self.target.warn_count += 1
        self.target.save()

    def kick(self, chat_id=None):
        self.bot.unban_chat_member(
            chat_id=chat_id or self._chat_id,
            user_id=self.target.id,
        )

    def mute(self, chat_id=None):
        self.bot.restrict_chat_member(
            chat_id=chat_id or self._chat_id,
            user_id=self.target.id,
            permissions=ChatPermissions(can_send_messages=False),
        )

    def ban(self, chat_id=None):
        self.bot.ban_chat_member(
            chat_id=chat_id or self._chat_id,
            user_id=self.target.id,
        )

    def free(self, chat_id=None):
        self.bot.unban_chat_member(
            chat_id=chat_id or self._chat_id,
            user_id=self.target.id,
            only_if_banned=True,
        )
        self.bot.restrict_chat_member(
            chat_id=chat_id or self._chat_id,
            user_id=self.target.id,
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

    def superban(self):
        for group in DBGroup.objects.filter(members__id=self.target.id):
            self.ban(group.id)

        self.target.banned = True
        self.target.save()

    def superfree(self):
        for group in DBGroup.objects.filter(members__id=self.target.id):
            self.free(group.id)

        self.target.banned = False
        self.target.save()


def handle_moderation_command(update: Update, context: CallbackContext) -> None:
    message: Message = update.message
    issuer: User = message.from_user
    chat: Chat = message.chat
    bot: Bot = context.bot

    try:
        command: ModerationCommand = ModerationCommand(bot, message)
    except NoTargetsInCommand:
        context.bot.send_message(
            chat_id=chat.id,
            text=(
                "❓ <b>Errore: utente non trovato</b>"
                "\n<b>Sintassi dei comandi di moderazione</b>:"
                "\n- <code>/comando @username [motivazione]</code>"
                "\n- <code>/comando menzione [motivazione]</code>"
                "\n- <code>/comando [motivazione]</code> <i>(in risposta a un messaggio)</i>"
                "\nRicorda che il campo <code>[motivazione]</code>, "
                "nonostante sia vivamente consigliato, è facoltativo."
            ),
            parse_mode="html",
        )
        return
    except PermissionError:
        # Insufficient permissions
        return

    prepared_entry = None
    if command.event != EventTypes.MODERATION_INFO:
        prepared_entry: Message = logging.prepare(msg=command.target_message)

    command.dispatch()
    message.delete()

    if command.event == EventTypes.MODERATION_INFO:
        # No moderation message or further logging needed
        return

    logging.log(
        command.event,
        chat=chat,
        target=command.target,
        issuer=issuer,
        reason=command.reason,
        msg=command.target_message,
        prepared_entry=prepared_entry,
    )

    if command.event == EventTypes.MODERATION_DEL:
        # No moderation message needed
        return

    target: DBUser = command.target
    text = (
        f"{command.event.value[1]} <b>Utente</b> {target.generate_mention()} "
        f"({target.warn_count}{' ⚠' if target.warn_count >= 3 else ''}) "
        f"<b>{command.event.value[2]}</b> "
        f"{f'per <i>{command.reason}</i>' if command.reason else ''}"
        f"\n➡️ <a href=\"https://studentiunimi.it/rules/\">Regolamento del network</a>"
    )
    sent_msg: Message = bot.send_message(
        chat_id=chat.id,
        text=text,
        parse_mode="html",
        disable_web_page_preview=True,
    )
    tasks.delete_message(chat.id, sent_msg.message_id)


def handle_creation_command(update: Update, context: CallbackContext) -> None:
    message: Message = update.message
    sender: User = message.from_user
    chat: Chat = message.chat

    if not utils.can_superban(sender):
        return

    text = utils.generate_group_creation_message(chat)
    msg = context.bot.send_message(chat_id=chat.id, text=text, parse_mode="html")
    msg.pin()
    message.delete()


def handle_whitelisting_command(update: Update, _: CallbackContext) -> None:
    message: Message = update.message
    sender: User = message.from_user
    chat: Chat = message.chat

    if not utils.can_superban(sender):
        return

    entities = message.parse_entities()

    for bot in entities:
        if bot.type != bot.MENTION:
            continue
        if entities[bot][-3:] != "bot":
            continue
        dbuser = DBUser.objects.get(id=sender.id)
        to_whitelist = BotWhitelist()
        to_whitelist.username = entities[bot]
        to_whitelist.whitelisted_by = dbuser
        to_whitelist.save()
        logging.log(logging.WHITELIST_BOT, chat, issuer=sender, bot=bot)
    message.delete()


def handle_toggle_admin_tagging(update: Update, _: CallbackContext) -> None:
    message: Message = update.message
    sender: User = message.from_user
    chat: Chat = message.chat

    if not utils.can_moderate(sender, chat):
        return

    try:
        dbgroup = DBGroup.objects.get(id=chat.id)
    except DBGroup.DoesNotExist:
        message.delete()
        return
    dbgroup.ignore_admin_tagging = not dbgroup.ignore_admin_tagging
    dbgroup.save()

    if dbgroup.ignore_admin_tagging:
        new_msg = chat.send_message("@admin are now ignored in this group")
    else:
        new_msg = chat.send_message("@admin are now not ignored in this group")
    tasks.delete_message(chat_id=chat.id, message_id=new_msg.message_id)
    message.delete()

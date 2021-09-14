import telegram
import telegram.ext
from telegram import Update
from telegram.ext import MessageHandler, Filters, CommandHandler, ChatMemberHandler, CallbackQueryHandler
from telegram.ext.dispatcher import Dispatcher

from telegrambot.handlers import messages, members, moderation


def dispatch_telegram_update(json_update: dict, token: str) -> None:
    bot = telegram.Bot(token=token)
    dispatcher = Dispatcher(bot, None, workers=0)

    # Pre-processing
    dispatcher.add_handler(MessageHandler(
        filters=Filters.chat_type.groups,
        callback=messages.handle_group_messages,
    ), group=0)

    # Groups
    dispatcher.add_handler(ChatMemberHandler(
        callback=members.handle_chat_member_updates,
        chat_member_types=ChatMemberHandler.ANY_CHAT_MEMBER,
    ), group=1)
    dispatcher.add_handler(CallbackQueryHandler(members.handle_verification, pattern="^verify$"))

    # Admin commands
    dispatcher.add_handler(CommandHandler(
        command="warn",
        callback=moderation.handle_warn_command,
    ), group=2)
    dispatcher.add_handler(CommandHandler(
        command="kick",
        callback=moderation.handle_kick_command,
    ), group=2)
    dispatcher.add_handler(CommandHandler(
        command="ban",
        callback=moderation.handle_ban_command,
    ), group=2)
    dispatcher.add_handler(CommandHandler(
        command="superban",
        callback=moderation.handle_global_ban_command,
    ), group=2)
    dispatcher.add_handler(CommandHandler(
        command="mute",
        callback=moderation.handle_mute_command,
    ), group=2)
    dispatcher.add_handler(CommandHandler(
        command="free",
        callback=moderation.handle_free_command,
    ), group=2)
    dispatcher.add_handler(CommandHandler(
        command="info",
        callback=moderation.handle_info_command,
    ), group=2)
    dispatcher.add_handler(CommandHandler(
        command="claim",
        callback=members.claim_command,
    ), group=2)
    dispatcher.add_handler(CommandHandler(
        command="creation",
        callback=moderation.handle_creation_command,
    ), group=2)

    update = Update.de_json(json_update, bot)
    dispatcher.process_update(update)

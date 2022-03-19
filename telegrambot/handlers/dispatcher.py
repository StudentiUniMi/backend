import logging as logg

from telegram import Update
from telegram.ext import MessageHandler, Filters, CommandHandler, ChatMemberHandler, CallbackQueryHandler, Updater

from telegrambot.handlers import messages, members, moderation, errors, memes


LOG = logg.getLogger(__name__)
dispatchers = {}


def setup_dispatcher(dispatcher):
    dispatcher.add_error_handler(errors.telegram_error_handler)

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
    dispatcher.add_handler(MessageHandler(
        filters=Filters.status_update,
        callback=members.handle_left_chat_member_updates,
    ), group=1)
    dispatcher.add_handler(MessageHandler(
        filters=Filters.chat_type.groups,
        callback=messages.handle_admin_tagging,
    ), group=1)

    # Admin commands
    dispatcher.add_handler(CommandHandler(
        command=[
            "info",
            "warn",
            "kick",
            "ban",
            "mute",
            "free",
            "superban",
            "superfree",
            "del",
        ],
        callback=moderation.handle_moderation_command,
    ), group=2)
    dispatcher.add_handler(CommandHandler(
        command="claim",
        callback=members.claim_command,
    ), group=2)
    dispatcher.add_handler(CommandHandler(
        command="creation",
        callback=moderation.handle_creation_command,
    ), group=2)
    dispatcher.add_handler(CommandHandler(
        command="whitelistbot",
        callback=moderation.handle_whitelisting_command,
    ), group=2)
    dispatcher.add_handler(CommandHandler(
        command="ignore_admin",
        callback=moderation.handle_toggle_admin_tagging,
    ), group=2)
    dispatcher.add_handler(CommandHandler(
        command="broadcast",
        callback=messages.broadcast_message,
    ), group=2)

    # User commands
    dispatcher.add_handler(CommandHandler(
        command="respects",
        callback=memes.init_respects,
    ), group=3)
    dispatcher.add_handler(CallbackQueryHandler(
        callback=memes.add_respect,
        pattern="^press_f$",
    ), group=3)


# Tokens that are sent to this function have been already checked againts the DB
def dispatch_telegram_update(json_update: dict, token: str) -> None:
    if token not in dispatchers.keys():
        dispatchers[token] = Updater(token=token).dispatcher
        setup_dispatcher(dispatchers[token])

    update = Update.de_json(json_update, dispatchers[token].bot)
    dispatchers[token].process_update(update)

import logging as logg
from telegram import Update
from telegram.ext import (
    MessageHandler,
    Filters,
    CommandHandler,
    ChatMemberHandler,
    CallbackQueryHandler,
    Updater,
    ChatJoinRequestHandler,
)

from telegrambot.handlers import (
    messages,
    members,
    moderation,
    errors,
    memes,
    welcome,
    settings,
)

LOG = logg.getLogger(__name__)
dispatchers = {}


def setup_dispatcher(dispatcher):
    dispatcher.add_error_handler(errors.telegram_error_handler)

    # Pre-processing
    ## All group messages
    dispatcher.add_handler(MessageHandler(
        filters=Filters.chat_type.groups,
        callback=messages.handle_group_messages,
    ), group=0)

    ## Group join requests
    dispatcher.add_handler(ChatJoinRequestHandler(
        callback=welcome.handle_join_request,
    ), group=1)

    ## Status updates
    dispatcher.add_handler(ChatMemberHandler(
        callback=members.handle_chat_member_updates,
        chat_member_types=ChatMemberHandler.ANY_CHAT_MEMBER,
    ), group=1)
    dispatcher.add_handler(MessageHandler(
        filters=Filters.status_update,
        callback=members.handle_left_chat_member_updates,
    ), group=1)

    ## Admin tagging
    dispatcher.add_handler(MessageHandler(
        filters=Filters.chat_type.groups,
        callback=messages.handle_admin_tagging,
    ), group=1)


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
        command="superfree",
        callback=moderation.handle_global_free_command,
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
    dispatcher.add_handler(CommandHandler(
        command="whitelistbot",
        callback=moderation.handle_whitelisting_command,
    ), group=2)
    dispatcher.add_handler(CommandHandler(
        command="ignore_admin",
        callback=moderation.handle_toggle_admin_tagging,
    ), group=2)
    dispatcher.add_handler(CommandHandler(
        command="delete",
        callback=moderation.handle_delete_command,
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


    # Private chat callback
    ## Language setting
    dispatcher.add_handler(CallbackQueryHandler(
        pattern=r"^ask_language$",
        callback=settings.ask_language,
    ), group=4)
    dispatcher.add_handler(CallbackQueryHandler(
        pattern=r"^set_language@",
        callback=settings.set_language,
    ), group=4)

    ## Gender setting
    dispatcher.add_handler(CallbackQueryHandler(
        pattern=r"^ask_gender$",
        callback=settings.ask_gender,
    ), group=4)
    dispatcher.add_handler(CallbackQueryHandler(
        pattern=r"^set_gender@",
        callback=settings.set_gender,
    ), group=4)

    ## Degree selection
    dispatcher.add_handler(CallbackQueryHandler(
        pattern=r"^ask_degree_type$",
        callback=settings.ask_degree_type,
    ), group=4)
    dispatcher.add_handler(CallbackQueryHandler(
        pattern=r"^ask_degree@",
        callback=settings.ask_degree,
    ), group=4)
    dispatcher.add_handler(CallbackQueryHandler(
        pattern=r"^set_degree@",
        callback=settings.set_degree,
    ), group=4)
    dispatcher.add_handler(CallbackQueryHandler(
        pattern=r"^accept_rules$",
        callback=welcome.accept_rules,
    ), group=4)



# Tokens that are sent to this function have been already checked againts the DB
def dispatch_telegram_update(json_update: dict, token: str) -> None:
    if token not in dispatchers.keys():
        dispatchers[token] = Updater(token=token).dispatcher
        setup_dispatcher(dispatchers[token])

    update = Update.de_json(json_update, dispatchers[token].bot)
    dispatchers[token].process_update(update)

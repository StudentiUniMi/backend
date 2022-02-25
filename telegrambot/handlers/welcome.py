from telegram import (
    Update,
    ChatJoinRequest,
    User,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from telegram.ext import (
    ConversationHandler,
    CallbackContext,
)

from telegrambot.models import User as DBUser


def handle_join_request(update: Update, context: CallbackContext) -> int:
    join_request: ChatJoinRequest = update.chat_join_request
    user: User = join_request.from_user
    db_user: DBUser = DBUser.objects.get(id=user.id)
    if db_user.rules_accepted:
        join_request.approve()
        del context.user_data["conversation"]
        return ConversationHandler.END

    context.bot.send_message(
        chat_id=user.id,
        # TODO: proper text
        text="Benvenuto nel network StudentiUniMi!\nTODO: testo di introduzione\nQuale è la tua lingua?",
        parse_mode="html",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text="🇮🇹 Italiano",
                    callback_data="set_language@IT",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🇬🇧 English",
                    callback_data="set_language@EN",
                ),
            ]
        ]),
    )
    context.user_data["conversation"]: str = "welcome"
    context.user_data["joining_chat_id"]: int = join_request.chat.id


def ask_rules_acceptance(update: Update, _: CallbackContext):
    update.callback_query.message.edit_text(
        text="Essere in una community significa rispettare delle regole."
             "\nPer entrare nei gruppi del network devi accettare il regolamento ufficiale "
             "che trovi qui bla bla bla"
             "\n\nAccetta le regole per essere ammesso nel gruppo e in tutti gli altri gruppi del Network",
        parse_mode="html",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text="✅ Accetto",
                    callback_data="accept_rules",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Torna indietro",
                    callback_data="ask_degree_type",
                )
            ],
        ])
    )


def accept_rules(update: Update, context: CallbackContext):
    callback_query: CallbackQuery = update.callback_query

    joining_chat_id: int = context.user_data.get("joining_chat_id")
    if context.user_data.get("conversation") != "welcome" or not joining_chat_id:
        callback_query.answer("❌ Please click on the invite link again.", show_alert=True)
        return

    user: User = update.callback_query.from_user
    dbuser: DBUser = DBUser.objects.get(id=user.id)
    dbuser.rules_accepted = True
    dbuser.save()

    context.bot.approve_chat_join_request(
        chat_id=joining_chat_id,
        user_id=user.id,
    )
    callback_query.answer("👋 Benvenuto!")
    callback_query.message.edit_text(
        text="Tutto fatto. Puoi ora entrare nel gruppo.",
    )

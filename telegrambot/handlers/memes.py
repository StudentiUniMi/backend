from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext


def init_respects(update: Update, context: CallbackContext) -> None:
    chat = update.message.chat
    chat.send_message(
        "Press F to pay respects.\n0 users have paid their respects",
        disable_notification=True,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text="🇫",
                    callback_data="press_f",
                )
            ]
        ])
    )


def add_respect(update: Update, context: CallbackContext) -> None:
    message = update.callback_query.message
    text = message.text

    count = int(text.split("\n")[1].split(" ")[0])
    count += 1

    message.edit_text(
        f"Press F to pay respects.\n{count} users have paid their respects",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text="🇫",
                    callback_data="press_f",
                )
            ]
        ])
    )

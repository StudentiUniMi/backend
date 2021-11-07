from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, TelegramError
from telegram.ext import CallbackContext, DispatcherHandlerStop


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

    try:
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
    except TelegramError:
        # Should probably resend the request with the updated counter
        # but doing so would be a pain, 'cause the library checks update_ids
        # so making fake requests would be too much effort for a meme command.
        # Therefore we just ignore the requests that raise exceptions. The users
        # will think that they're the only ones that clicked the button when in
        # reality, more could have pressed it at the same time.
        raise DispatcherHandlerStop

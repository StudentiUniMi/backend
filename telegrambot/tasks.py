from background_task import background

from telegrambot.handlers.utils import get_bot


@background(schedule=90)
def delete_message(chat_id: int, message_id: int) -> None:
    """Schedule a message deletion in the future"""
    bot = get_bot(chat_id)
    bot.delete_message(chat_id=chat_id, message_id=message_id)

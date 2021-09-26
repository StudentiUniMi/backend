from typing import List
import time

import telegram.error
from background_task import background
from background_task.models import Task

from telegrambot.handlers.utils import get_bot
from telegrambot.models import (
    Group as DBGroup,
)


@background(schedule=90)
def delete_message(chat_id: int, message_id: int) -> None:
    """Schedule a message deletion in the future"""
    bot = get_bot(chat_id)
    try:
        bot.delete_message(chat_id=chat_id, message_id=message_id)
    except telegram.error.BadRequest:  # the message was already deleted
        pass


@background(schedule=1)
def fetch_telegram_info() -> None:
    dbgroups = list(DBGroup.objects.all())
    print(f"Processing {len(dbgroups)} groups")

    for dbgroup in dbgroups:
        try:
            res = dbgroup.update_info()
            if not res:
                print(f"Bad chat {dbgroup.id}")
        except telegram.error.RetryAfter as e:
            time.sleep(e.retry_after + 10)
        except telegram.error.Unauthorized:
            print(f"Bot is not member of chat {dbgroup.id}")
    print("DONE\n" + '-' * 15)


Task.objects.all().filter(task_name="telegrambot.tasks.fetch_telegram_info").delete()
fetch_telegram_info(schedule=1, verbose_name="Fetch Telegram group info", repeat=Task.HOURLY)

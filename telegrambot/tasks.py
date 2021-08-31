from typing import List
import time

import telegram.error
from background_task import background
from background_task.models import Task

from telegrambot.handlers.utils import get_bot
from telegrambot.models import (
    User as DBUser,
    Group as DBGroup,
    GroupMembership as DBGroupMembership,
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
        if not dbgroup.bot:
            continue

        bot = telegram.Bot(dbgroup.bot.token)
        try:
            chat: telegram.Chat = bot.get_chat(chat_id=dbgroup.id)
            administrators: List[telegram.ChatMember] = bot.get_chat_administrators(chat_id=dbgroup.id)
        except telegram.error.BadRequest:
            print(f"Bad chat {dbgroup.id}")
            continue

        dbgroup.title = chat.title
        dbgroup.invite_link = chat.invite_link
        dbgroup.description = chat.description

        for member in administrators:
            user = member.user
            dbmember = DBUser.objects.get_or_create(id=user.id, first_name=user.first_name)[0]
            if member.status == member.CREATOR:
                dbgroup.owner = dbmember

            dbmembership = DBGroupMembership.objects.get_or_create(group_id=chat.id, user=dbmember)[0]
            dbmembership.status = member.status
            dbmembership.save()

        dbgroup.save()
        time.sleep(0.3)

    print("DONE\n" + '-' * 15)


Task.objects.all().filter(task_name="telegrambot.tasks.fetch_telegram_info").delete()
fetch_telegram_info(schedule=1, verbose_name="Fetch Telegram group info", repeat=Task.HOURLY)

from typing import Optional, Union

from telegram import Message
from telegram.ext import MessageFilter
from telegram.ext.filters import DataDict


class NewChatMemberFilter(MessageFilter):
    def filter(self, message: Message) -> Optional[Union[bool, DataDict]]:
        return len(message.new_chat_members) > 0

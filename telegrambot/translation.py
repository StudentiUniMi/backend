from modeltranslation.translator import register, TranslationOptions
from telegrambot.models import Group, MessageFilter


@register(Group)
class GroupTranslationOptions(TranslationOptions):
    fields = ("welcome_model", )


@register(MessageFilter)
class MessageFilterTranslationOptions(TranslationOptions):
    fields = ("message", )

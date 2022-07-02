from modeltranslation.translator import register, TranslationOptions
from telegrambot.models import Group


@register(Group)
class GroupTranslationOptions(TranslationOptions):
    fields = ("welcome_model", )

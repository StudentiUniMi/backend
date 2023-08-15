from modeltranslation.translator import register, TranslationOptions
from telegrambot.models import Group

from django.conf import settings


@register(Group)
class GroupTranslationOptions(TranslationOptions):
    fields = (
        "welcome_model",
    )


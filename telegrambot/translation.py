from modeltranslation.translator import register, TranslationOptions
from telegrambot.models import Group

from django.conf import settings


@register(Group)
class GroupTranslationOptions(TranslationOptions):
    fields = (
        "welcome_model",
        "extra_group_name",
        "extra_group_description",
    )


def serialize_translated_field(obj, field):
    return {
        lang[0]: getattr(obj, "%s_%s" % (field, lang[0]))
        for lang in settings.LANGUAGES
    }

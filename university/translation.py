from modeltranslation.translator import register, TranslationOptions
from university.models import FeaturedGroup

from django.conf import settings


@register(FeaturedGroup)
class FeaturedGroupTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "description",
        "button_name",
    )


def serialize_translated_field(obj, field):
    return {
        lang[0]: getattr(obj, "%s_%s" % (field, lang[0]))
        for lang in settings.LANGUAGES
    }

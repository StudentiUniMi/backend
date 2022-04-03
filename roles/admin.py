from django.contrib import admin
from polymorphic.admin import (
    PolymorphicParentModelAdmin,
    PolymorphicChildModelAdmin,
    PolymorphicChildModelFilter,
)

from roles.models import (
    BaseRole,
    Representative,
    Professor,
    Moderator,
    Administrator,
    SuperAdministrator,
)


@admin.register(BaseRole)
class BaseRoleAdmin(PolymorphicParentModelAdmin):
    base_model = BaseRole
    child_models = (
        Representative,
        Professor,
        Moderator,
        Administrator,
        SuperAdministrator,
    )
    list_filter = (PolymorphicChildModelFilter, )
    list_display = ("tg_user", "polymorphic_type",  "django_user", )


class BaseRoleChildAdmin(PolymorphicChildModelAdmin):
    base_model = BaseRole
    base_fieldsets = (
        (None, {
            "fields": ("tg_user", "django_user"),
        }),
        ("Permissions scope", {
            "fields": ("all_groups", "extra_groups", "degrees", ),
        }),
        ("Custom title override", {
            "fields": ("custom_title_override", ),
        }),
        ("Moderation permissions override", {
            "classes": ("collapse", ),
            "fields": ("moderation_info", "moderation_del", "moderation_warn",
                       "moderation_kick", "moderation_ban", "moderation_mute", "moderation_free",
                       "moderation_superban", "moderation_superfree", ),
        }),
        ("Telegram permissions override", {
            "classes": ("collapse", ),
            "fields": ("can_change_info", "can_invite_users", "can_pin_messages", "can_manage_chat",
                       "can_delete_messages", "can_manage_voice_chats", "can_restrict_members",
                       "can_promote_members", ),
        })
    )
    autocomplete_fields = ("tg_user", "django_user", "degrees", )


@admin.register(Representative)
class RepresentativeAdmin(BaseRoleChildAdmin):
    base_model = Representative
    base_fieldsets = (
        BaseRoleChildAdmin.base_fieldsets[0],
        ("Representative", {
            "fields": ("political_list", "political_role", )
        }),
        *BaseRoleChildAdmin.base_fieldsets[1:],
    )
    show_in_index = False


@admin.register(Professor)
class ProfessorAdmin(BaseRoleChildAdmin):
    base_model = Professor
    show_in_index = False


@admin.register(Moderator)
class ModeratorAdmin(BaseRoleChildAdmin):
    base_model = Moderator
    show_in_index = False


@admin.register(Administrator)
class AdministratorAdmin(BaseRoleChildAdmin):
    base_model = Administrator
    show_in_index = False


@admin.register(SuperAdministrator)
class SuperAdministratorAdmin(BaseRoleChildAdmin):
    base_model = SuperAdministrator
    show_in_index = False

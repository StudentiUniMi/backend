from datetime import datetime

import telegram
from django.apps import apps
from django.db import models


class User(models.Model):
    class Meta:
        ordering = ["id"]
        verbose_name = "Telegram user"
        verbose_name_plural = "Telegram users"
        indexes = [
            models.Index(fields=["id"], name="id_idx"),
            models.Index(fields=["id", "banned"], name="banned_idx"),
            models.Index(fields=["first_name", "last_name"], name="name_idx"),
        ]

    id = models.PositiveBigIntegerField("Telegram user ID", primary_key=True, unique=True)
    first_name = models.CharField("first name", max_length=256)
    last_name = models.CharField("last name", max_length=256, blank=True, null=True)
    username = models.CharField("username", max_length=64, blank=True, null=True)
    reputation = models.IntegerField("reputation", default=0)
    warn_count = models.IntegerField("warn count", default=0)
    banned = models.BooleanField("banned?", default=False)
    permissions_level = models.IntegerField("permission level", default=0)
    last_seen = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return f"{self.first_name}{f' {self.last_name}' if self.last_name else ''} [{self.id}]"

    def get_privileges(self, chat):
        if self.privileges.count() == 0:
            return False

        if group_privileges := self.privileges.filter(
                scope=UserPrivilege.PrivilegeScopes.GROUPS,
                authorized_groups__id__in=[chat.id, ]
        ):
            return group_privileges[0]

        Degree = apps.get_model("university", "Degree")  # Avoid circular imports
        degrees = Degree.objects.filter(courses__group__id=chat.id)

        if degree_privileges := self.privileges.filter(
                scope=UserPrivilege.PrivilegeScopes.DEGREES,
                authorized_degrees__in=degrees,
        ):
            return degree_privileges[0]

        if department_privileges := self.privileges.filter(
                scope=UserPrivilege.PrivilegeScopes.DEPARTMENTS,
                authorized_departments__degrees__in=degrees,
        ):
            return department_privileges[0]

        if privileges := self.privileges.filter(scope=UserPrivilege.PrivilegeScopes.ALL):
            return privileges[0]

        return False


class Group(models.Model):
    class Meta:
        ordering = ["id"]
        verbose_name = "Telegram group"
        verbose_name_plural = "Telegram groups"

    def _format_filename(self, filename):
        return f"gropics/{self.id}_{filename}"

    id = models.BigIntegerField("Telegram group ID", primary_key=True, unique=True)
    title = models.CharField("title", max_length=512)
    description = models.TextField("description", max_length=2048, blank=True, null=True)
    profile_picture = models.ImageField(upload_to=_format_filename, blank=True, null=True)
    invite_link = models.CharField("invite link", max_length=128, blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="groups_owned", blank=True, null=True)
    members = models.ManyToManyField(User, through="GroupMembership", related_name="member_of")

    def __str__(self):
        return f"{self.title} [{self.id}]"


class GroupMembership(models.Model):
    class Meta:
        verbose_name = "Telegram group membership"
        verbose_name_plural = "Telegram groups memberships"

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    last_seen = models.DateTimeField("last seen", default=datetime.now)
    messages_count = models.PositiveIntegerField("messages count", default=0)

    def __str__(self):
        return f"{self.user} in {self.group}"


class UserPrivilege(models.Model):
    """
    This model allows you to set granular permissions and custom titles to special users
    (such as representatives, professors, tutor, etc...).
    An user can have multiple instances of this class associated;
    in case of multiple associations the most specific one is considered (see scope field).
    """

    class Meta:
        verbose_name = "User privilege"
        verbose_name_plural = "User privileges"

    class PrivilegeTypes(models.TextChoices):
        ADMIN = 'A', "Amministratore"
        PROFESSOR = 'P', "Docente"
        REPRESENTATIVE = 'R', "Rappresentante"
        TUTOR = 'T', "Tutor"
        OTHER = 'O', "Other"

    class PrivilegeScopes(models.TextChoices):
        GROUPS = 'G', "Solo i gruppi autorizzati"
        DEGREES = 'Dg', "Solo i c.d.L. autorizzati"
        DEPARTMENTS = 'Di', "Solo i dipartimenti autorizzati"
        ALL = 'A', "Tutto l'Ateneo"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="privileges")
    type = models.CharField("type", choices=PrivilegeTypes.choices, max_length=2, default=PrivilegeTypes.ADMIN)

    scope = models.CharField(
        "privileges scope",
        choices=PrivilegeScopes.choices,
        max_length=2,
        help_text="Dove si dovrebbero applicare i permessi?"
                  "\nIn caso di sovrapposizione, si applica il permesso più specifico.",
        default=PrivilegeScopes.GROUPS,
    )
    authorized_groups = models.ManyToManyField(
        Group,
        related_name="privileged_users",
        blank=True,
    )
    authorized_degrees = models.ManyToManyField(
        "university.Degree",
        related_name="privileged_users",
        blank=True,
    )
    authorized_departments = models.ManyToManyField(
        "university.Department",
        related_name="privileged_users",
        blank=True,
    )

    # Telegram privileges
    custom_title = models.CharField("custom title", max_length=16, blank=True, null=True)
    can_change_info = models.BooleanField(
        help_text="True, if the user is allowed to change the chat title, photo and other settings",
    )
    can_invite_users = models.BooleanField(
        help_text="True, if the user is allowed to invite new users to the chat",
    )
    can_pin_messages = models.BooleanField(
        help_text="True, if the user is allowed to pin messages; groups and supergroups only",
    )
    can_manage_chat = models.BooleanField(
        help_text="True, if the administrator can access the chat event log, chat statistics, message statistics in "
                  "channels, see channel members, see anonymous administrators in supergroups and ignore slow mode. "
                  "Implied by any other administrator privilege",
    )
    can_delete_messages = models.BooleanField(
        help_text="True, if the administrator can delete messages of other users",
    )
    can_manage_voice_chats = models.BooleanField(
        help_text="True, if the administrator can manage voice chats",
    )
    can_restrict_members = models.BooleanField(
        help_text="True, if the administrator can restrict, ban or unban chat members",
    )
    can_promote_members = models.BooleanField(
        help_text="True, if the administrator can add new administrators with a subset of their own privileges or "
                  "demote administrators that he has promoted, directly or indirectly "
                  "(promoted by administrators that were appointed by the user)",
    )

    def __str__(self):
        return f"{self.PrivilegeTypes(self.type).name.title()} {str(self.user)}, " \
               f"{self.PrivilegeScopes(self.scope).name.lower()} scope"


class TelegramBot(models.Model):
    """
    This model represents an authorized Telegram bot
    """
    class Meta:
        verbose_name = "Telegram bot"
        verbose_name_plural = "Telegram bots"

    token = models.CharField("token", max_length=64, primary_key=True)
    notes = models.TextField("notes", blank=True, null=True)

    @property
    def username(self):
        bot = telegram.Bot(self.token)
        return f"@{bot.username}"

    @property
    def censured_token(self):
        bot_id, secret = self.token.split(":")
        return f"{bot_id}:{'•' * (len(secret)-5)}{secret[-5:]}"

    def __str__(self):
        return self.username

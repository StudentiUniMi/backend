from datetime import datetime
from typing import List

import telegram
from telegram import ChatMember
from django.db import models
from telegrambot import handlers


class Languages(models.TextChoices):
    EN = "en", "English"
    IT = "it", "Italian"


class User(models.Model):
    """A Telegram user.
    Every user seen by the bot should be automatically saved or updated in the database.
    An user can be special: see UserPrivileges class and get_privileges method for more information.
    """
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
    language = models.CharField("language", max_length=3, blank=True, null=True)
    reputation = models.IntegerField("reputation", default=0)
    warn_count = models.IntegerField("warn count", default=0)
    banned = models.BooleanField("banned?", default=False)
    permissions_level = models.IntegerField("permission level", default=0)
    last_seen = models.DateTimeField(default=datetime.now)

    def __str__(self) -> str:
        return f"{self.first_name}{f' {self.last_name}' if self.last_name else ''} [{self.id}]"

    @property
    def name(self):
        """The full name of the user"""
        return f"{self.first_name}{f' {self.last_name}' if self.last_name else ''}"

    def generate_mention(self):
        """Generate an HTML mention of the user"""
        return f"<a href=\"tg://user?id={self.id}\">{f'@{self.username}' if self.username else self.name}</a>"


class Group(models.Model):
    """A Telegram group.
    Unlike the User class, the objects of this class are not created automatically,
    but they're inserted by an administrator on the admin interface.
    If the bot receives an update from an unknown group, it should ignore it
    and alert the bot administrators.
    """
    class Meta:
        ordering = ["id"]
        verbose_name = "Telegram group"
        verbose_name_plural = "Telegram groups"

    def _format_filename(self, filename):
        """Helper function used to generate an appropriate filename for a group profile picture"""
        return f"gropics/{self.id}_{filename}"

    id = models.BigIntegerField(
        "Telegram group ID",
        primary_key=True,
        unique=True,
        help_text="Set the ID to 0 if you want an userbot to actually create the group",
    )
    title = models.CharField("title", max_length=512)
    description = models.TextField("description", max_length=2048, blank=True, null=True)
    language = models.CharField("preferred language", default="it", choices=Languages.choices,
                                max_length=3, blank=True, null=True)
    profile_picture = models.ImageField(upload_to=_format_filename, blank=True, null=True)
    invite_link = models.CharField("invite link", max_length=128, blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="groups_owned", blank=True, null=True)
    members = models.ManyToManyField(User, through="GroupMembership", related_name="member_of")
    bot = models.ForeignKey("TelegramBot", on_delete=models.SET_NULL, related_name="groups", blank=False, null=True)
    ignore_admin_tagging = models.BooleanField("Ignore @admin tagging", default=False, null=False)
    welcome_model = models.TextField("Welcome model", default=(
        "<b>{greetings}</b> nel gruppo {title}"
        "\n\nIscriviti al canale @studenti_unimi"
    ), help_text="Available format parameters: {greetings} and {title}")

    def __str__(self) -> str:
        return f"{self.title} [{self.id}]"

    def generate_welcome_message(self, members: List[User]) -> str:
        """Generate a customized welcome message by filling the welcome_model.

        :param members: list of new members who just joined the group
        :return: the welcome message
        """
        greetings = f"{'Benvenuto' if len(members) == 1 else 'Benvenuti'} " \
                    f"{', '.join([m.first_name for m in members])}"
        return self.welcome_model.format(
            greetings=greetings,
            title=self.title,
        )

    def update_info(self):
        """Update Telegram info"""
        if not self.bot:
            return False

        bot = telegram.Bot(self.bot.token)
        try:
            chat: telegram.Chat = bot.get_chat(chat_id=self.id)
            administrators: List[telegram.ChatMember] = bot.get_chat_administrators(chat_id=self.id)
        except telegram.error.BadRequest:
            print(f"Bad chat {self.id}")
            return False

        self.title = chat.title
        self.invite_link = chat.invite_link
        self.description = chat.description

        for member in administrators:
            user = member.user
            dbmember = User.objects.get_or_create(id=user.id)[0]
            if member.status == member.CREATOR:
                self.owner = dbmember

            dbmembership = GroupMembership.objects.get_or_create(group_id=chat.id, user=dbmember)[0]
            dbmembership.status = member.status
            dbmembership.save()
        self.save()
        return True


class GroupMembership(models.Model):
    """A relation between an user and a group.
    Should be created when an user enters (or is recognized) in a group.
    """
    class Meta:
        verbose_name = "Telegram group membership"
        verbose_name_plural = "Telegram groups memberships"
        unique_together = ("user", "group")

    class MembershipStatus(models.TextChoices):
        CREATOR = ChatMember.CREATOR
        ADMINISTRATOR = ChatMember.ADMINISTRATOR
        MEMBER = ChatMember.MEMBER
        RESTRICTED = ChatMember.RESTRICTED
        LEFT = ChatMember.LEFT
        KICKED = ChatMember.KICKED  # it means 'banned'

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    last_seen = models.DateTimeField("last seen", default=datetime.now)
    messages_count = models.PositiveIntegerField("messages count", default=0)
    status = models.CharField(
        "status",
        max_length=16,
        choices=MembershipStatus.choices,
        default=MembershipStatus.MEMBER,
    )

    def __str__(self) -> str:
        return f"{self.user} in {self.group}"


class UserPrivilege(models.Model):
    """User privileges (deprecated).
    This model allows you to set granular permissions and custom titles to special users
    (such as representatives, professors, tutor, etc...).

    An user can have multiple instances of this class associated.
    In case of multiple associations the most specific one is considered, based on scope field.

    TODO: remove this model
    """

    class Meta:
        verbose_name = "User privilege (deprecated)"
        verbose_name_plural = "User privileges (deprecated)"

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
    can_superban_members = models.BooleanField(
        help_text="True, if the administrator can ban a member from all groups of the network. This should be set"
                  " only for the members of the C.A.N.",
        default=False
    )

    def __str__(self):
        return f"{self.PrivilegeTypes(self.type).name.title()} {str(self.user)}, " \
               f"{self.PrivilegeScopes(self.scope).name.lower()} scope"

    def save(self, *args, **kwargs) -> None:
        """Save the current instance and set the proper permissions in all groups the user is in"""
        super().save(*args, **kwargs)
        # groups = self.user.member_of.all()
        # for group in groups:
        #     utils.set_admin_rights(self.user, group)

    def delete(self, *args, **kwargs) -> None:
        """Save the current instance and revoke all special permissions in all groups the user is in"""
        # groups = self.user.member_of.all()
        # for group in groups:
        #     utils.remove_admin_rights(self.user, group)
        super().delete(*args, **kwargs)


class TelegramBot(models.Model):
    """An authorized Telegram bot.
    The instances of this model must NEVER be returned by the API.
    """
    class Meta:
        verbose_name = "Telegram bot"
        verbose_name_plural = "Telegram bots"

    token = models.CharField("token", max_length=64, primary_key=True)
    notes = models.TextField("notes", blank=True, null=True)
    username = models.CharField("username", max_length=32, blank=True)

    def save(self, *args, **kwargs):
        bot = telegram.Bot(self.token)
        try:
            self.username = f"@{bot.username}"
        except (telegram.error.Unauthorized, telegram.error.InvalidToken):
            self.username = "[Invalid bot token]"
        super().save(*args, **kwargs)

    @property
    def censured_token(self) -> str:
        """Return a censured version of the token, with only the last five characters visible.
        Remains unsafe to show to unauthenticated users variations of the bot token.
        """
        bot_id, secret = self.token.split(":")
        return f"{bot_id}:{'•' * (len(secret)-5)}{secret[-5:]}"

    def __str__(self) -> str:
        return self.username


class TelegramUserbot(models.Model):
    """An authorized Telegram userbot worker

    https://github.com/StudentiUniMi/userbot-worker
    """
    class Meta:
        verbose_name = "Telegram userbot"
        verbose_name_plural = "Telegram userbots"

    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    session_file = models.FileField("telethon session file", upload_to="userbot-sessions/")
    active = models.BooleanField("active", default=False)
    group_count = models.IntegerField("group count", default=0)
    last_used = models.DateTimeField("last used", default=datetime.now)


class BotWhitelist(models.Model):
    """A list of bots that won't be auto-kicked upon joining a group of the network"""
    class Meta:
        verbose_name = "Whitelisted bot"
        verbose_name_plural = "Whitelisted bots"

    username = models.CharField("username", max_length=64, null=False, unique=True)
    whitelisted_by = models.ForeignKey(User, on_delete=models.SET_NULL, to_field="id", null=True)


class TelegramLog(models.Model):
    """Logs for various things like joined/left channel or moderation commands"""
    class Events(models.IntegerChoices):
        CHAT_DOES_NOT_EXIST = 0, "CHAT_DOES_NOT_EXIST"
        MODERATION_INFO = 5, "MODERATION_INFO"
        MODERATION_WARN = 1, "MODERATION_WARN"
        MODERATION_KICK = 2, "MODERATION_KICK"
        MODERATION_BAN = 3, "MODERATION_BAN"
        MODERATION_MUTE = 4, "MODERATION_MUTE"
        MODERATION_FREE = 6, "MODERATION_FREE"
        MODERATION_SUPERBAN = 7, "MODERATION_SUPERBAN"
        MODERATION_SUPERFREE = 11, "MODERATION_SUPERFREE"
        USER_JOINED = 8, "USER_JOINED"
        USER_LEFT = 9, "USER_LEFT"
        NOT_ENOUGH_RIGHTS = 10, "NOT_ENOUGH_RIGHTS"
        TELEGRAM_ERROR = 12, "TELEGRAM_ERROR"
        USER_CALLED_ADMIN = 13, "USER_CALLED_ADMIN"
        MODERATION_DEL = 14, "MODERATION_DEL"
        WHITELIST_BOT = 15, "WHITELIST_BOT"
        BROADCAST = 16, "BROADCAST"

    id = models.BigAutoField(primary_key=True)
    event = models.IntegerField(choices=Events.choices)
    chat = models.ForeignKey(Group, null=True, on_delete=models.SET_NULL)
    target = models.ForeignKey(User, related_name="log_as_target", null=True, on_delete=models.RESTRICT)
    issuer = models.ForeignKey(User, related_name="log_as_issuer", null=True, on_delete=models.RESTRICT)
    reason = models.TextField(null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    message_deleted = models.BooleanField(null=True, blank=True)
    timestamp = models.DateTimeField(null=False)

    def __str__(self):
        text = ""
        if self.issuer:
            text += f"{self.issuer.__str__()} -> "
        text += f"{self.Events(self.event).name}"
        if self.target:
            text += f" -> {self.target.__str__()}"
        return text

    def iso_timestamp(self):
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    iso_timestamp.short_description = "Timestamp"


class BlacklistedUser(models.Model):
    """A Blacklisted Telegram User, who can't join our groups"""
    class Meta:
        verbose_name = "Blacklisted user"
        verbose_name_plural = "Blacklisted users"

    class BlacklistSource(models.TextChoices):
        ADMINISTRATOR = 'A', 'Administrator'
        GROUPHELP = 'GH', 'GroupHelp'

    user_id = models.PositiveBigIntegerField("Telegram user ID", primary_key=True, unique=True)
    source = models.CharField("source", choices=BlacklistSource.choices, max_length=2)

    def __str__(self):
        return f"{self.user_id} ({self.get_source_display()})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        try:
            dbuser = User.objects.get(id=self.user_id)
            handlers.utils.check_blacklist(dbuser)
        except User.DoesNotExist:
            pass

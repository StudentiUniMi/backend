from django.db import models

from datetime import datetime


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

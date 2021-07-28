from rest_framework import serializers

from telegram.models import (
    Group,
)


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ("id", "title", "profile_picture", "invite_link")

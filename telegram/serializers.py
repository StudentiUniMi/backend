from rest_framework import serializers

from telegram.models import (
    User,
    Group,
)


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ("id", "title", "profile_picture", "invite_link")


class UserSerialzier(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "username", )

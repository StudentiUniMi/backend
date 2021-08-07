from rest_framework import serializers

from telegrambot.models import (
    User,
    Group,
)


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ("id", "title", "profile_picture", "invite_link")


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "username", )

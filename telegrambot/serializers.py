from rest_framework import serializers

from telegrambot.translation import serialize_translated_field
from telegrambot.models import (
    User,
    Group,
    GroupMembership,
)


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ("id", "title", "profile_picture", "invite_link")


class ExtraGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ("id", "name", "description", "invite_link", "user_count", )

    name = serializers.SerializerMethodField("get_names")
    description = serializers.SerializerMethodField("get_descriptions")
    user_count = serializers.SerializerMethodField("get_user_count")


    def get_names(self, obj):
        return serialize_translated_field(obj, "extra_group_name")


    def get_descriptions(self, obj):
        return serialize_translated_field(obj, "extra_group_description")


    def get_user_count(self, obj):
        return obj.members.filter(groupmembership__status__in=[
            GroupMembership.MembershipStatus.CREATOR,
            GroupMembership.MembershipStatus.ADMINISTRATOR,
            GroupMembership.MembershipStatus.MEMBER,
            GroupMembership.MembershipStatus.RESTRICTED,
        ]).count()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "username", )

from rest_framework import serializers

from university.translation import serialize_translated_field
from telegrambot.serializers import (
    GroupSerializer as TgGroupSerializer,
    UserSerializer as TgUserSerializer,
)
from university.models import (
    Representative,
    Professor,
    Course,
    Degree,
    Department,
    CourseDegree,
    CourseLink,
    FeaturedGroup,
)
from telegrambot.models import GroupMembership


class RepresentativeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Representative
        fields = ("tguser", "degree_name", )

    tguser = TgUserSerializer()


class ProfessorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Professor
        fields = ("first_name", "last_name", "url", )

    url = serializers.URLField()


class CourseLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseLink
        fields = ("name", "url", )


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ("pk", "name", "cfu", "wiki_link", "links", "group", "professor", )

    group = TgGroupSerializer()
    links = CourseLinkSerializer(many=True)
    professor = ProfessorSerializer()


class CourseDegreeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseDegree
        fields = ("course", "year", "semester", )

    course = CourseSerializer()


class DegreeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Degree
        fields = ("pk", "name", "type", "group", "slug", "icon", )

    group = TgGroupSerializer()


class DepartmentSerializer(serializers.ModelSerializer):
    degree_count = serializers.SerializerMethodField()
    representative_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ("pk", "name", "slug", "icon", "degree_count", "representative_count", )

    @staticmethod
    def get_degree_count(obj):
        return obj.degrees.count()

    @staticmethod
    def get_representative_count(obj):
        return obj.representatives.count()


class VerboseDegreeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Degree
        fields = ("pk", "name", "type", "department", "group", "slug", )

    department = DepartmentSerializer()
    group = TgGroupSerializer()


class VerboseDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ("pk", "name", "slug", "icon", "representatives", "degrees",)

    degrees = DegreeSerializer(many=True, read_only=True)
    representatives = RepresentativeSerializer(many=True)


class FeaturedGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeaturedGroup
        fields = ("id", "name", "description", "invite_link", "user_count",
                  "image_url", "external_url", "button_name")

    id = serializers.IntegerField(source="group.id")
    name = serializers.SerializerMethodField("get_names")
    description = serializers.SerializerMethodField("get_descriptions")
    invite_link = serializers.CharField(source="group.invite_link")
    user_count = serializers.SerializerMethodField("get_user_count")
    button_name = serializers.SerializerMethodField("get_button_names")


    @staticmethod
    def get_names(obj):
        return serialize_translated_field(obj, "name")


    @staticmethod
    def get_descriptions(obj):
        return serialize_translated_field(obj, "description")


    @staticmethod
    def get_button_names(obj):
        return serialize_translated_field(obj, "button_name")


    @staticmethod
    def get_user_count(obj):
        return obj.group.members.filter(groupmembership__status__in=[
            GroupMembership.MembershipStatus.CREATOR,
            GroupMembership.MembershipStatus.ADMINISTRATOR,
            GroupMembership.MembershipStatus.MEMBER,
            GroupMembership.MembershipStatus.RESTRICTED,
        ]).count()

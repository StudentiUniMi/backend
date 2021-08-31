from rest_framework import serializers

from telegrambot.serializers import (
    GroupSerializer as TgGroupSerializer,
    UserSerializer as TgUserSerializer,
)
from university.models import (
    Representative,
    Course,
    Degree,
    Department,
    CourseDegree,
    CourseLink,
)


class RepresentativeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Representative
        fields = ("tguser", "degree_name", )

    tguser = TgUserSerializer()


class CourseLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseLink
        fields = ("name", "url", )


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ("pk", "name", "cfu", "wiki_link", "links", "group", )

    group = TgGroupSerializer()
    links = CourseLinkSerializer(many=True)


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

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
        fields = ("tguser", "title")

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
        fields = ("pk", "name", "type", "slug", )


class VerboseDegreeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Degree
        fields = ("pk", "name", "type", "courses", "slug", )

    courses = CourseDegreeSerializer(source="coursedegree_set", many=True, read_only=True)


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ("pk", "name", )


class VerboseDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ("pk", "name", "representatives", "degrees", )

    degrees = DegreeSerializer(many=True, read_only=True)
    representatives = RepresentativeSerializer(many=True)

from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from university.models import Degree, Department, Course, Representative
from university.serializers import (
    DegreeSerializer,
    VerboseDegreeSerializer,
    DepartmentSerializer,
    VerboseDepartmentSerializer, CourseSerializer, RepresentativeSerializer,
)


def _get_all_objects(model, serializer):
    queryset = model.objects.all()
    serializer = serializer(queryset, many=True)
    return Response(serializer.data)


def _get_verbose_object(model, serializer, pk):
    queryset = model.objects.all()
    obj = get_object_or_404(queryset, pk=pk)
    serializer = serializer(obj)
    return Response(serializer.data)


@api_view(["GET"])
def degrees_by_department(request):
    department_id = request.query_params.get("dep_id", None)
    if not department_id:
        return Response({"ok": False, "error": "Please provide a dep_id (department id)"}, status=400)

    queryset = Degree.objects.all().filter(department_id=department_id)
    serializer = DegreeSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def degree_by_slug(request):
    slug = request.query_params.get("slug", None)
    if not slug:
        return Response({"ok": False, "error": "Please provide an unique slug"}, status=400)

    try:
        degree = Degree.objects.get(slug=slug)
    except Degree.DoesNotExist:
        return Response({"ok": False, "error": "Not found"}, status=404)
    serializer = VerboseDegreeSerializer(degree)
    return Response(serializer.data)


@api_view(["GET"])
def courses_by_degree(request):
    degree_id = request.query_params.get("deg_id", None)
    if not degree_id:
        return Response({"ok": False, "error": "Please provide a deg_id (degree id)"}, status=400)

    queryset = Course.objects.all().filter(degrees__in=[degree_id, ])
    serializer = CourseSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def representatives_by_department(request):
    department_id = request.query_params.get("dep_id", None)
    if not department_id:
        return Response({"ok": False, "error": "Please provide a dep_id (department id)"}, status=400)

    queryset = Representative.objects.all().filter(department_id=department_id)
    serializer = RepresentativeSerializer(queryset, many=True)
    return Response(serializer.data)


class DepartmentViewSet(viewsets.ViewSet):
    @staticmethod
    def list(_):
        return _get_all_objects(Department, DepartmentSerializer)

    @staticmethod
    def retrieve(_, pk=None):
        return _get_verbose_object(Department, VerboseDepartmentSerializer, pk)

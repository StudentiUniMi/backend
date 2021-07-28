from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response

from university.models import Degree, Department
from university.serializers import (
    DegreeSerializer,
    VerboseDegreeSerializer,
    DepartmentSerializer,
    VerboseDepartmentSerializer,
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


class DegreeViewSet(viewsets.ViewSet):
    @staticmethod
    def list(_):
        return _get_all_objects(Degree, DegreeSerializer)

    @staticmethod
    def retrieve(_, pk=None):
        return _get_verbose_object(Degree, VerboseDegreeSerializer, pk)


class DepartmentViewSet(viewsets.ViewSet):
    @staticmethod
    def list(_):
        return _get_all_objects(Department, DepartmentSerializer)

    @staticmethod
    def retrieve(_, pk=None):
        return _get_verbose_object(Department, VerboseDepartmentSerializer, pk)

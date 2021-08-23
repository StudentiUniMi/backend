import json

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpRequest
from django.core.exceptions import PermissionDenied
from django.db.utils import IntegrityError
from django.db import transaction
from rest_framework import viewsets
from rest_framework.response import Response

from university.models import Degree, Department, DEGREE_TYPES
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


def parse_json(request: HttpRequest):
    """The data passed to this endpoint is the output of the script that can be found
    at https://github.com/StudentiUniMi/cdl-scraper
    """
    if not request.user.is_authenticated:
        raise PermissionDenied
    if request.method == "POST":
        try:
            data = json.loads(request.POST["json_data"])
        except json.JSONDecodeError:
            return HttpResponse("The data that was provided is not a well-formed JSON object!")

        unparsed = []

        for course in data:
            if course["dipartimento"] == "":
                continue
            dep = Department()
            dep.name = course["dipartimento"]
            try:
                with transaction.atomic():
                    dep.save()  # If already present it raises IntegrityError
            except IntegrityError:
                dep = Department.objects.get(name=course["dipartimento"])

            deg = Degree()
            deg.name = course["corso"]
            if course["tipo"] == "Laurea triennale":
                deg.type = DEGREE_TYPES[0][0]
            elif course["tipo"] == "Laurea magistrale":
                deg.type = DEGREE_TYPES[1][0]
            elif course["tipo"] == "Laurea magistrale a ciclo unico":
                deg.type = DEGREE_TYPES[2][0]
            else:
                unparsed.append(course)
                continue
            deg.department = dep
            try:
                deg.save()
            except IntegrityError:
                pass

        if len(unparsed) > 0:
            text = "<br><br>The following JSON objects couldn't be added, please do so manually:<br>"
            for course in unparsed:
                text += "&emsp;" + str(course) + "<br>"
        else:
            text = ""
        return HttpResponse("Data has been added succesfully!" + text)  # Should probably give back a proper HTML page
    else:
        return render(request, 'models/degree_json_parser.html')


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

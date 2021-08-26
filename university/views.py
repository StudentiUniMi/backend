import json

from django.core.exceptions import PermissionDenied
from django.db.utils import IntegrityError
from django.http import HttpResponse, HttpRequest
from django.shortcuts import get_object_or_404, render
from rest_framework import viewsets
from rest_framework.response import Response

from university.models import Degree, Department, Course, DEGREE_TYPES
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


def import_degrees(request: HttpRequest):
    """The data passed to this endpoint is the output of the script that can be found
    at https://github.com/StudentiUniMi/cdl-scraper
    """
    user = request.user
    if not user.is_authenticated or not user.has_perm("university.add_course"):
        raise PermissionDenied

    if request.method == "GET":
        return render(request, 'models/degrees_json_parser.html')

    try:
        data = json.loads(request.POST["json_data"])
    except json.JSONDecodeError:
        return HttpResponse("The data that was provided is not a well-formed JSON object!")

    unparsed = []
    for course in data:
        if len(course["dipartimento"]) == 0:
            continue

        dep = Department.objects.get_or_create(defaults={"name": course["dipartimento"]})[0]
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
    return HttpResponse("Data has been added successfully!" + text)  # Should probably give back a proper HTML page


def import_courses(request: HttpRequest):
    """The data passed to this endpoint is the output of the script that can be found
    at https://github.com/StudentiUniMi/cdl-scraper
    """
    user = request.user
    if not user.is_authenticated or not user.has_perm("university.add_course"):
        raise PermissionDenied

    if request.method == "GET":
        return render(request, 'models/courses_json_parser.html')

    try:
        data = json.loads(request.POST["json_data"])
    except json.JSONDecodeError:
        return HttpResponse("The data that was provided is not a well-formed JSON object!")

    for c in data.keys():
        course = Course()
        course.name = c
        course.cfu = 0 if data[c]["cfu"] == "" else int(data[c]["cfu"])
        try:
            course.save()
        except IntegrityError:
            pass
    return HttpResponse("Data has been added successfully!")


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

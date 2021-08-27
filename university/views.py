import json

from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
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
        return render(request, 'models/import_json.html', {"type": "degree"})

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse("The data that was provided is not a well-formed JSON object!")

    unparsed = []
    ignored = 0
    added = 0
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
            added += 1
        except IntegrityError:
            ignored += 1

    if len(unparsed) > 0:
        text = "<br><br>The following JSON objects couldn't be added, please do so manually:<br>"
        for course in unparsed:
            text += "&emsp;" + str(course) + "<br>"
    else:
        text = ""
    text += "\n{} degrees where already present and have been ignored.".format(ignored)
    text += "\n{} degrees have been added to the database.".format(added)
    return HttpResponse("Data has been added successfully!" + text)


def import_courses(request: HttpRequest):
    """The data passed to this endpoint is the output of the script that can be found
    at https://github.com/StudentiUniMi/cdl-scraper
    """
    user = request.user
    if not user.is_authenticated or not user.has_perm("university.add_course"):
        raise PermissionDenied

    if request.method == "GET":
        return render(request, 'models/import_json.html', {"type": "course"})

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse("The data that was provided is not a well-formed JSON object!")

    ignored = 0
    added = 0
    for c in data:
        try:
            _, created = Course.objects.get_or_create(
                name=c["title"],
                cfu=0 if c["cfu"] == "" else int(c["cfu"]),
                slug_unimi=c["title"]
            )
            if created:
                added += 1
            else:
                ignored += 1
        except IntegrityError:
            ignored += 1
    text = "\n{} courses were already present and have been ignored.\n{} courses have been added to the database."\
        .format(ignored, added)
    return HttpResponse("Data has been added successfully!" + text)


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

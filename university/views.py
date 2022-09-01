import json
import random
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.db.models.functions import Length
from django.db.utils import IntegrityError
from django.http import HttpResponse, HttpRequest
from django.shortcuts import get_object_or_404, render
from polymorphic.query import PolymorphicQuerySet
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from roles.models import (
    BaseRole,
    Moderator,
    Administrator,
    SuperAdministrator,
)
from university.models import (
    DEGREE_TYPES,
    Degree,
    Department,
    Course,
    Representative,
    CourseDegree,
)
from university.serializers import (
    DegreeSerializer,
    VerboseDegreeSerializer,
    DepartmentSerializer,
    VerboseDepartmentSerializer,
    RepresentativeSerializer,
    CourseDegreeSerializer,
)
from telegrambot.serializers import UserSerializer


def _get_all_objects(model, serializer):
    queryset = model.objects.all().order_by("name")
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
        if len(course["department"]) == 0:
            continue

        dep = Department.objects.get_or_create(defaults={"name": course["department"]})[0]
        deg = Degree()
        deg.name = course["degree"]
        if course["type"] == "Laurea triennale":
            deg.type = DEGREE_TYPES[0][0]
        elif course["type"] == "Laurea magistrale":
            deg.type = DEGREE_TYPES[1][0]
        elif course["type"] == "Laurea magistrale a ciclo unico":
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
                slug_unimi=c["slug"]
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


@api_view(["GET"])
def typing_degrees(request):
    """Return 30 random degrees"""
    pks = Degree.objects.values_list("pk", flat=True)
    sampled_pks = random.sample(list(pks), min(len(pks), 30))
    degrees = [d.name.lower() for d in Degree.objects.filter(pk__in=sampled_pks).distinct("name")]
    random.shuffle(degrees)
    return Response(degrees)


@api_view(["GET"])
def degrees_by_department(request):
    department_id = request.query_params.get("dep_id", None)
    if not department_id:
        return Response({"ok": False, "error": "Please provide a dep_id (department id)"}, status=400)

    queryset = Degree.objects.all().filter(department_id=department_id)\
        .select_related("group")\
        .annotate(courses_count=Count("courses"))\
        .order_by("-courses_count", "name")
    serializer = DegreeSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def degree_by_slug_or_pk(request):
    slug = request.query_params.get("slug", None)
    pk = request.query_params.get("pk", None)
    if not slug and not pk:
        return Response({"ok": False, "error": "Please provide the pk or an unique slug"}, status=400)

    try:
        degree = Degree.objects.get(pk=int(pk)) if pk else Degree.objects.get(slug=slug)
    except (Degree.DoesNotExist, TypeError):
        return Response({"ok": False, "error": "Not found"}, status=404)
    serializer = VerboseDegreeSerializer(degree)
    return Response(serializer.data)


@api_view(["GET"])
def degrees_by_query(request):
    query = request.query_params.get("q", None)
    if not query:
        return Response([])

    queryset = Degree.objects.all()\
        .filter(name__icontains=query)\
        .select_related("group")\
        .order_by(Length("name").asc(), "name", "type")
    serializer = DegreeSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def admin_by_degree(request):
    slug = request.query_params.get("slug", None)
    pk = request.query_params.get("pk", None)
    if not slug and not pk:
        return Response({"ok": False, "error": "Please provide the pk or an unique slug"})

    try:
        degree = Degree.objects.get(pk=int(pk)) if pk else Degree.objects.get(slug=slug)
    except (Degree.DoesNotExist, TypeError):
        return Response({"ok": False, "error": "Not found"}, status=404)

    roles: PolymorphicQuerySet[BaseRole] = BaseRole.objects.filter(
        (Q(degrees__in=[degree]) | Q(all_groups=True))
    )
    roles = roles.instance_of(Moderator) | roles.instance_of(Administrator) | roles.instance_of(SuperAdministrator)
    serializer = UserSerializer([role.tg_user for role in roles], many=True)
    return Response(serializer.data)


@api_view(["GET"])
def courses_by_degree(request):
    degree_id = request.query_params.get("deg_id", None)
    if not degree_id:
        return Response({"ok": False, "error": "Please provide a deg_id (degree id)"}, status=400)

    queryset = CourseDegree.objects.all().filter(degree_id=degree_id)\
        .prefetch_related("course", "course__degrees", "course__links", )\
        .select_related("course__group")\
        .order_by("course__name")
    queryset = sorted(queryset, key=lambda c: (c.year if c.year >= 0 else c.year + 10) * 2 + c.semester)
    serializer = CourseDegreeSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def representatives_by_department(request):
    department_id = request.query_params.get("dep_id", None)
    if not department_id:
        return Response({"ok": False, "error": "Please provide a dep_id (department id)"}, status=400)

    queryset = Representative.objects.all()\
        .filter(department_id=department_id)\
        .select_related("tguser")
    serializer = RepresentativeSerializer(queryset, many=True)
    return Response(serializer.data)


class DepartmentViewSet(viewsets.ViewSet):
    @staticmethod
    def list(_):
        return _get_all_objects(Department, DepartmentSerializer)

    @staticmethod
    def retrieve(_, pk=None):
        return _get_verbose_object(Department, VerboseDepartmentSerializer, pk)

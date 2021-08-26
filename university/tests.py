from django.contrib.auth.models import User, AnonymousUser, Permission
from django.core.exceptions import PermissionDenied
from django.test import TestCase, Client, RequestFactory
from rest_framework.renderers import JSONRenderer as Renderer

from telegrambot.models import (
    Group as TgGroup,
    User as TgUser,
)
from university import test_data
from university import views as university_views
from university.models import (
    Course,
    CourseDegree,
    CourseLink,
    Degree,
    Department,
    Representative,
)
from university.serializers import (
    CourseSerializer,
    DegreeSerializer,
    VerboseDegreeSerializer,
    DepartmentSerializer,
    VerboseDepartmentSerializer,
)


# Test models


class CourseTestCase(TestCase):
    def setUp(self):
        dep1 = Department.objects.create(pk=1, name="Computer Science Department")
        deg1 = Degree.objects.create(
            pk=1,
            name="Computer Science",
            type='B',
            slug="computer_science",
            department=dep1,
        )
        deg2 = Degree.objects.create(
            pk=2,
            name="Music Information Science",
            type='B',
            slug="music_information_science",
            department=dep1,
        )
        group1 = TgGroup.objects.create(
            id=42069,
            title="Computer Architecture II fan club",
            description="The best course ever\nBy @studenti_unimi",
            invite_link="https://example.com/join/qwerty",
        )

        self.course1 = Course.objects.create(
            pk=1,
            name="Programming I",
            cfu=12,
        )
        CourseDegree.objects.create(degree=deg1, course=self.course1, year=1, semester=1)
        CourseLink.objects.create(
            course=self.course1,
            name="Ariel (1° ed.)",
            url="https//ariel.example.com/courses/programming_1_firsted",
        )
        CourseLink.objects.create(
            course=self.course1,
            name="Ariel (2° ed.)",
            url="https://ariel.example.com/courses/programming_1_seconded",
        )

        self.course2 = Course.objects.create(
            pk=2,
            name="Linear Algebra I",
            cfu=6,
            wiki_link="https://example.com/wiki/linear_algebra_i.php",
        )
        CourseDegree.objects.create(degree=deg1, course=self.course2, year=1, semester=2)
        CourseDegree.objects.create(degree=deg2, course=self.course2, year=1, semester=1)
        CourseLink.objects.create(
            course=self.course2,
            name="Ariel",
            url="https://ariel.example.com/courses/linear_algebra_1"
        )

        self.course3 = Course.objects.create(
            pk=3,
            name="Computer Architecture II",
            cfu=6,
            group=group1,
        )

    def test_str_degrees(self):
        self.assertEqual(self.course1.str_degrees, "Computer Science")
        self.assertEqual(self.course2.str_degrees, "Computer Science, Music Information Science")
        self.assertEqual(self.course3.str_degrees, '')

    def test_str(self):
        self.assertEqual(str(self.course1), "Programming I (Computer Science)")
        self.assertEqual(str(self.course2), "Linear Algebra I (Computer Science, Music Information Science)")
        self.assertEqual(str(self.course3), "Computer Architecture II ()")

    def test_serializer(self):
        self.maxDiff = None  # Show all diffs
        self.assertJSONEqual(Renderer().render(CourseSerializer([
            self.course1,
            self.course2,
            self.course3,
        ], many=True).data), [
            {
                "pk": 1,
                "name": "Programming I",
                "cfu": 12,
                "wiki_link": None,
                "links": [
                    {
                        "name": "Ariel (1° ed.)",
                        "url": "https//ariel.example.com/courses/programming_1_firsted",
                    },
                    {
                        "name": "Ariel (2° ed.)",
                        "url": "https://ariel.example.com/courses/programming_1_seconded",
                    },
                ],
                "group": None,
            },
            {
                "pk": 2,
                "name": "Linear Algebra I",
                "cfu": 6,
                "wiki_link": "https://example.com/wiki/linear_algebra_i.php",
                "links": [
                    {
                        "name": "Ariel",
                        "url": "https://ariel.example.com/courses/linear_algebra_1",
                    },
                ],
                "group": None,
            },
            {
                "pk": 3,
                "name": "Computer Architecture II",
                "cfu": 6,
                "wiki_link": None,
                "links": [],
                "group": {
                    "id": 42069,
                    "title": "Computer Architecture II fan club",
                    "profile_picture": None,
                    "invite_link": "https://example.com/join/qwerty",
                },
            }
        ])


class DegreeTestCase(TestCase):
    def setUp(self):
        dep1 = Department.objects.create(name="Computer Science Department")
        dep2 = Department.objects.create(name="Medicine Department")

        self.deg1 = Degree.objects.create(
            pk=1,
            name="Computer Science",
            type='B',
            slug="computer_science_b",
            department=dep1,
        )
        self.deg2 = Degree.objects.create(
            pk=2,
            name="Computer Science",
            type='M',
            slug="computer_science_m",
            department=dep1,
        )
        self.deg3 = Degree.objects.create(
            pk=3,
            name="Medicine",
            type='C',
            slug="medicine",
            department=dep2,
        )

        self.course1 = Course.objects.create(
            pk=1,
            name="Programming I",
            cfu=12,
        )
        CourseDegree.objects.create(degree=self.deg1, course=self.course1, year=1, semester=1)
        CourseLink.objects.create(
            course=self.course1,
            name="Ariel (1° ed.)",
            url="https//ariel.example.com/courses/programming_1_firsted",
        )

        group1 = TgGroup.objects.create(
            id=69420,
            title="Linear Algebra I fan club",
            description="AAAAAAAAaaaAAAAAAAAAAAA\nBy @studenti_unimi",
            invite_link="https://example.com/join/azerty",
        )
        self.course2 = Course.objects.create(
            pk=2,
            name="Linear Algebra I",
            cfu=6,
            wiki_link="https://example.com/wiki/linear_algebra_i.php",
            group=group1,
        )
        CourseDegree.objects.create(degree=self.deg1, course=self.course2, year=1, semester=2)
        CourseDegree.objects.create(degree=self.deg2, course=self.course2, year=1, semester=1)

    def test_str(self):
        self.assertEqual(str(self.deg1), "Computer Science [Triennale]")
        self.assertEqual(str(self.deg2), "Computer Science [Magistrale]")
        self.assertEqual(str(self.deg3), "Medicine [Laurea a ciclo unico]")

    def test_serializer(self):
        self.maxDiff = None
        self.assertJSONEqual(Renderer().render(DegreeSerializer([
            self.deg1,
            self.deg2,
            self.deg3,
        ], many=True).data), [
            {
                "pk": 1,
                "name": "Computer Science",
                "type": 'B',
                "slug": "computer_science_b",
            },
            {
                "pk": 2,
                "name": "Computer Science",
                "type": 'M',
                "slug": "computer_science_m",
            },
            {
                "pk": 3,
                "name": "Medicine",
                "type": 'C',
                "slug": "medicine",
            }
        ])

    def test_verbose_serializer(self):
        self.maxDiff = None
        self.assertJSONEqual(Renderer().render(VerboseDegreeSerializer(self.deg1).data), {
            "pk": 1,
            "name": "Computer Science",
            "type": 'B',
            "slug": "computer_science_b",
            "courses": [
                {
                    "course": {
                        "pk": 1,
                        "name": "Programming I",
                        "cfu": 12,
                        "wiki_link": None,
                        "links": [
                            {
                                "name": "Ariel (1° ed.)",
                                "url": "https//ariel.example.com/courses/programming_1_firsted",
                            },
                        ],
                        "group": None,
                    },
                    "year": 1,
                    "semester": 1,
                },
                {
                    "course": {
                        "pk": 2,
                        "name": "Linear Algebra I",
                        "cfu": 6,
                        "wiki_link": "https://example.com/wiki/linear_algebra_i.php",
                        "links": [],
                        "group": {
                            "id": 69420,
                            "title": "Linear Algebra I fan club",
                            "profile_picture": None,
                            "invite_link": "https://example.com/join/azerty",
                        },
                    },
                    "year": 1,
                    "semester": 2,
                },
            ],
        })


class DepartmentTestCase(TestCase):
    def setUp(self):
        self.dep1 = Department.objects.create(pk=1, name="Computer Science Department")
        self.dep2 = Department.objects.create(pk=2, name="Medicine Department")
        self.dep3 = Department.objects.create(pk=3, name="Physics Department")

        Degree.objects.create(
            pk=1,
            name="Computer Science",
            type='B',
            slug="computer_science_b",
            department=self.dep1,
        )
        Degree.objects.create(
            pk=2,
            name="Computer Science",
            type='M',
            slug="computer_science_m",
            department=self.dep1,
        )
        Degree.objects.create(
            pk=3,
            name="Medicine",
            type='C',
            slug="medicine",
            department=self.dep2,
        )
        tgus1 = TgUser.objects.create(
            id=26170256,
            first_name="Marco",
            last_name="Aceti",
            username="acetimarco",
        )
        Representative.objects.create(
            department=self.dep2,
            tguser=tgus1,
            title="Representative",
        )
        tgus2 = TgUser.objects.create(
            id=108121631,
            first_name="Davide",
            last_name="Busolin",
            username="davidebusolin",
        )
        Representative.objects.create(
            department=self.dep2,
            tguser=tgus2,
            title="Chad",
        )

    def test_str(self):
        self.assertEqual(str(self.dep1), self.dep1.name)
        self.assertEqual(str(self.dep2), self.dep2.name)
        self.assertEqual(str(self.dep3), self.dep3.name)

    def test_serializer(self):
        self.maxDiff = None
        self.assertJSONEqual(Renderer().render(DepartmentSerializer([
            self.dep1,
            self.dep2,
            self.dep3,
        ], many=True).data), [
            {
                "pk": 1,
                "name": "Computer Science Department",
            },
            {
                "pk": 2,
                "name": "Medicine Department",
            },
            {
                "pk": 3,
                "name": "Physics Department",
            }
        ])

    def test_verbose_serializer(self):
        self.maxDiff = None
        self.assertJSONEqual(Renderer().render(VerboseDepartmentSerializer(self.dep1).data), {
            "pk": 1,
            "name": "Computer Science Department",
            "degrees": [
                {
                    "pk": 1,
                    "name": "Computer Science",
                    "type": 'B',
                    "slug": "computer_science_b",
                },
                {
                    "pk": 2,
                    "name": "Computer Science",
                    "type": 'M',
                    "slug": "computer_science_m",
                },
            ],
            "representatives": [],
        })
        self.assertJSONEqual(Renderer().render(VerboseDepartmentSerializer(self.dep2).data), {
            "pk": 2,
            "name": "Medicine Department",
            "representatives": [
                {
                    "tguser": {
                        "id": 26170256,
                        "first_name": "Marco",
                        "last_name": "Aceti",
                        "username": "acetimarco",
                    },
                    "title": "Representative"
                },
                {
                    "tguser": {
                        "id": 108121631,
                        "first_name": "Davide",
                        "last_name": "Busolin",
                        "username": "davidebusolin",
                    },
                    "title": "Chad",
                }
            ],
            "degrees": [
                {
                    "pk": 3,
                    "name": "Medicine",
                    "type": 'C',
                    "slug": "medicine",
                },
            ],
        })
        self.assertJSONEqual(Renderer().render(VerboseDepartmentSerializer(self.dep3).data), {
            "pk": 3,
            "name": "Physics Department",
            "degrees": [],
            "representatives": [],
        })


class DataEntryTestCase(TestCase):
    def setUp(self):
        user3 = User.objects.create(username="marco", password="backend")
        user3.user_permissions.add(Permission.objects.get(codename="add_course"))
        self.users = [
            (AnonymousUser(), False),  # anon user
            (User.objects.create(username="giuseppe", password="network"), False),  # unauthorized user
            (user3, True),  # authorized user
        ]
        self.factory = RequestFactory()

    def _request(self, path: str, json_data: str, render_view, excepted_response: bytes):
        request = self.factory.post(path, data=json_data, content_type="application/json")
        for user in self.users:
            request.user = user[0]
            try:
                response = render_view(request)
                self.assertEqual(response.content, excepted_response)
            except PermissionDenied:
                self.assertFalse(user[1])

    def test_correct_degrees_entry(self):
        self._request(
            path="/api/import/degrees",
            json_data=test_data.degree_data,
            render_view=university_views.import_degrees,
            excepted_response=b"Data has been added successfully!",
        )

    def test_malformed_degrees_json(self):
        self._request(
            path="/api/import/degrees",
            json_data="asd",
            render_view=university_views.import_degrees,
            excepted_response=b"The data that was provided is not a well-formed JSON object!",
        )

    def test_correct_courses_entry(self):
        self._request(
            path="/api/import/courses",
            json_data=test_data.course_data,
            render_view=university_views.import_courses,
            excepted_response=b"Data has been added successfully!",
        )

    def test_malformed_courses_json(self):
        self._request(
            path="/api/import/courses",
            json_data="asd",
            render_view=university_views.import_courses,
            excepted_response=b"The data that was provided is not a well-formed JSON object!",
        )

    # TODO: test the actual import of the data

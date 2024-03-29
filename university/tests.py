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
    Professor,
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

        prof = Professor.objects.create(
            first_name="Elio",
            last_name="Franzini",
            url="https://unimi.it/",
        )
        self.course2 = Course.objects.create(
            pk=2,
            name="Linear Algebra I",
            cfu=6,
            wiki_link="https://example.com/wiki/linear_algebra_i.php",
            professor=prof,
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
                "professor": None,
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
                "professor": {
                    "first_name": "Elio",
                    "last_name": "Franzini",
                    "url": "https://unimi.it/"
                },
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
                "professor": None,
            }
        ])


class DegreeTestCase(TestCase):
    def setUp(self):
        dep1 = Department.objects.create(
            pk=1,
            name="Computer Science Department",
            slug="computer_science",
        )
        dep2 = Department.objects.create(
            pk=2,
            name="Medicine Department",
            slug="medicine",
        )

        group1 = TgGroup.objects.create(
            id=999,
            title="Medicine general group",
            description="By @studenti_unimi",
            invite_link="https://example.com/join/medicine_unimi",
            profile_picture="/test.jpg",
        )

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
            icon="computer",
            department=dep1,
        )
        self.deg3 = Degree.objects.create(
            pk=3,
            name="Medicine",
            type='C',
            slug="medicine",
            department=dep2,
            group=group1,
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
                "group": None,
                "icon": None,
            },
            {
                "pk": 2,
                "name": "Computer Science",
                "type": 'M',
                "slug": "computer_science_m",
                "group": None,
                "icon": "computer",
            },
            {
                "pk": 3,
                "name": "Medicine",
                "type": 'C',
                "slug": "medicine",
                "group": {
                    "id": 999,
                    "title": "Medicine general group",
                    "profile_picture": "/test.jpg",
                    "invite_link": "https://example.com/join/medicine_unimi",
                },
                "icon": None,
            }
        ])

    def test_verbose_serializer(self):
        self.maxDiff = None
        self.assertJSONEqual(Renderer().render(VerboseDegreeSerializer(self.deg1).data), {
            "pk": 1,
            "name": "Computer Science",
            "type": 'B',
            "slug": "computer_science_b",
            "department": {
                "pk": 1,
                "name": "Computer Science Department",
                "degree_count": 2,
                "representative_count": 0,
                "slug": "computer_science",
                "icon": None,
            },
            "group": None,
        })
        self.assertJSONEqual(Renderer().render(VerboseDegreeSerializer(self.deg3).data), {
            "pk": 3,
            "name": "Medicine",
            "type": 'C',
            "slug": "medicine",
            "department": {
                "pk": 2,
                "name": "Medicine Department",
                "degree_count": 1,
                "representative_count": 0,
                "slug": "medicine",
                "icon": None,
            },
            "group": {
                "id": 999,
                "title": "Medicine general group",
                "profile_picture": "/test.jpg",
                "invite_link": "https://example.com/join/medicine_unimi",
            },
        })


class DepartmentTestCase(TestCase):
    def setUp(self):
        self.dep1 = Department.objects.create(
            pk=1,
            name="Computer Science Department",
            slug="computer_science",
        )
        self.dep2 = Department.objects.create(
            pk=2,
            name="Medicine Department",
            slug="medicine"
        )
        self.dep3 = Department.objects.create(
            pk=3,
            name="Physics Department",
            slug="physics",
            icon="meter",
        )

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
            degree_name="Representative",
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
            degree_name="Chad",
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
                "degree_count": 2,
                "representative_count": 0,
                "slug": "computer_science",
                "icon": None,
            },
            {
                "pk": 2,
                "name": "Medicine Department",
                "degree_count": 1,
                "representative_count": 2,
                "slug": "medicine",
                "icon": None,
            },
            {
                "pk": 3,
                "name": "Physics Department",
                "degree_count": 0,
                "representative_count": 0,
                "slug": "physics",
                "icon": "meter",
            }
        ])

    def test_verbose_serializer(self):
        self.maxDiff = None
        self.assertJSONEqual(Renderer().render(VerboseDepartmentSerializer(self.dep1).data), {
            "pk": 1,
            "name": "Computer Science Department",
            "slug": "computer_science",
            "icon": None,
            "degrees": [
                {
                    "pk": 1,
                    "name": "Computer Science",
                    "type": 'B',
                    "slug": "computer_science_b",
                    "icon": None,
                    "group": None,
                },
                {
                    "pk": 2,
                    "name": "Computer Science",
                    "type": 'M',
                    "slug": "computer_science_m",
                    "icon": None,
                    "group": None,
                },
            ],
            "representatives": [],
        })
        self.assertJSONEqual(Renderer().render(VerboseDepartmentSerializer(self.dep2).data), {
            "pk": 2,
            "name": "Medicine Department",
            "slug": "medicine",
            "icon": None,
            "representatives": [
                {
                    "tguser": {
                        "id": 26170256,
                        "first_name": "Marco",
                        "last_name": "Aceti",
                        "username": "acetimarco",
                    },
                    "degree_name": "Representative"
                },
                {
                    "tguser": {
                        "id": 108121631,
                        "first_name": "Davide",
                        "last_name": "Busolin",
                        "username": "davidebusolin",
                    },
                    "degree_name": "Chad",
                }
            ],
            "degrees": [
                {
                    "pk": 3,
                    "name": "Medicine",
                    "type": 'C',
                    "slug": "medicine",
                    "icon": None,
                    "group": None,
                },
            ],
        })
        self.assertJSONEqual(Renderer().render(VerboseDepartmentSerializer(self.dep3).data), {
            "pk": 3,
            "name": "Physics Department",
            "slug": "physics",
            "icon": "meter",
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
            excepted_response=b"Data has been added successfully!"
                              b"\n0 degrees where already present and have been ignored."
                              b"\n74 degrees have been added to the database.",
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
            excepted_response=b"Data has been added successfully!"
                              b"\n43 courses were already present and have been ignored."
                              b"\n5087 courses have been added to the database.",
        )

    def test_malformed_courses_json(self):
        self._request(
            path="/api/import/courses",
            json_data="asd",
            render_view=university_views.import_courses,
            excepted_response=b"The data that was provided is not a well-formed JSON object!",
        )

    # TODO: test the actual import of the data

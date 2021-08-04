from django.test import TestCase
from rest_framework.renderers import JSONRenderer as Renderer

from telegram.models import Group as TgGroup
from university.models import (
    Course,
    CourseDegree,
    Degree,
    Department,
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

        self.course2 = Course.objects.create(
            pk=2,
            name="Linear Algebra I",
            cfu=6,
            wiki_link="https://example.com/wiki/linear_algebra_i.php",
        )
        CourseDegree.objects.create(degree=deg1, course=self.course2, year=1, semester=2)
        CourseDegree.objects.create(degree=deg2, course=self.course2, year=1, semester=1)

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
                "group": None,
            },
            {
                "pk": 2,
                "name": "Linear Algebra I",
                "cfu": 6,
                "wiki_link": "https://example.com/wiki/linear_algebra_i.php",
                "group": None,
            },
            {
                "pk": 3,
                "name": "Computer Architecture II",
                "cfu": 6,
                "wiki_link": None,
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
        })
        self.assertJSONEqual(Renderer().render(VerboseDepartmentSerializer(self.dep2).data), {
            "pk": 2,
            "name": "Medicine Department",
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
        })

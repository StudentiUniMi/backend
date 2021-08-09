import os

from django.test import TestCase
from rest_framework.renderers import JSONRenderer as Renderer

from telegrambot.models import (
    User as TgUser,
    Group as TgGroup,
    TelegramBot, UserPrivilege,
)
from telegrambot.serializers import (
    UserSerializer,
    GroupSerializer,
)
from university.models import Department, Degree, Course, CourseDegree

TEST_BOT_TOKEN = os.environ.get("TEST_BOT_TOKEN", None)
if not TEST_BOT_TOKEN:
    raise AssertionError("Please set the TELEGRAM_TEST_BOT_TOKEN environment variable")
TEST_BOT_USERNAME = os.environ.get("TEST_BOT_USERNAME", None)
if not TEST_BOT_USERNAME:
    raise AssertionError("Please set the TELEGRAM_TEST_BOT_USERNAME environment variable")


class TelegramUserTestCase(TestCase):
    def setUp(self):
        self.maxDiff = None
        self.usr1 = TgUser.objects.create(
            id=26170256,
            first_name="Marco",
            last_name="Aceti",
            username="acetimarco",
        )
        self.usr2 = TgUser.objects.create(
            id=108121631,
            first_name="Davide",
            last_name="Busolin",
            username="davidebusolin",
        )
        self.usr3 = TgUser.objects.create(
            id=244426552,
            first_name="Sette",
        )

    def test_str(self):
        self.assertEqual(str(self.usr1), "Marco Aceti [26170256]")
        self.assertEqual(str(self.usr2), "Davide Busolin [108121631]")
        self.assertEqual(str(self.usr3), "Sette [244426552]")

    def test_serializer(self):
        self.assertJSONEqual(Renderer().render(UserSerializer(self.usr1).data), {
            "id": 26170256,
            "first_name": "Marco",
            "last_name": "Aceti",
            "username": "acetimarco",
        })
        self.assertJSONEqual(Renderer().render(UserSerializer(self.usr2).data), {
            "id": 108121631,
            "first_name": "Davide",
            "last_name": "Busolin",
            "username": "davidebusolin",
        })
        self.assertJSONEqual(Renderer().render(UserSerializer(self.usr3).data), {
            "id": 244426552,
            "first_name": "Sette",
            "last_name": None,
            "username": None,
        })


class TelegramGroupTestCase(TestCase):
    def setUp(self):
        self.maxDiff = None
        self.group1 = TgGroup.objects.create(
            id=1007654321,
            title="Programming I",
            description="By @studenti_unimi",
            profile_picture="/test.jpg",
        )
        self.group2 = TgGroup.objects.create(
            id=-1001234567,
            title="Physics II",
            description="By @studenti_unimi",
            invite_link="https://example.com/join/physics_2",
        )

    def test_str(self):
        self.assertJSONEqual(Renderer().render(GroupSerializer(self.group1).data), {
            "id": 1007654321,
            "title": "Programming I",
            "profile_picture": "/test.jpg",
            "invite_link": None,
        })
        self.assertJSONEqual(Renderer().render(GroupSerializer(self.group2).data), {
            "id": -1001234567,
            "title": "Physics II",
            "profile_picture": None,
            "invite_link": "https://example.com/join/physics_2",
        })

    def test_generate_welcome_message(self):
        class DummyMember:
            def __init__(self, name):
                self.first_name = name

        members = [DummyMember("Marco"), DummyMember("Davide"), DummyMember("Silvio")]
        self.assertEqual(self.group1.generate_welcome_message(members[0:1]), (
            "<b>Benvenuto Marco</b> nel gruppo Programming I"
            "\n\nIscriviti al canale @studenti_unimi"
        ))
        self.assertEqual(self.group1.generate_welcome_message(members[0:2]), (
            "<b>Benvenuti Marco, Davide</b> nel gruppo Programming I"
            "\n\nIscriviti al canale @studenti_unimi"
        ))
        self.assertEqual(self.group1.generate_welcome_message(members[0:3]), (
            "<b>Benvenuti Marco, Davide, Silvio</b> nel gruppo Programming I"
            "\n\nIscriviti al canale @studenti_unimi"
        ))


class UserPrivilegeTestCase(TestCase):
    def setUp(self):
        self.maxDiff = None
        self.group1 = TgGroup.objects.create(
            id=123,
            title="Programming I fan club",
        )
        self.group2 = TgGroup.objects.create(
            id=321,
            title="We <3 Linear Algebra",
        )
        self.group3 = TgGroup.objects.create(
            id=111,
            title="Anatomy I group"
        )

        dip1 = Department.objects.create(name="Computer Science Department")
        dip2 = Department.objects.create(name="Health Department")
        deg1 = Degree.objects.create(
            name="Computer science",
            type='B',
            department=dip1,
        )
        Degree.objects.create(
            name="Medicine",
            type='C',
            department=dip2,
        )
        course1 = Course.objects.create(
            name="Programming I",
            cfu=12,
            group=self.group1,
        )
        CourseDegree.objects.create(
            course=course1,
            degree=deg1,
            year=1, semester=1,
        )
        course2 = Course.objects.create(
            name="Linear Algebra I",
            cfu=6,
            group=self.group2,
        )
        CourseDegree.objects.create(
            course=course2,
            degree=deg1,
            year=1, semester=2,
        )

        self.usr1 = TgUser.objects.create(
            id=26170256,
            first_name="Marco",
            last_name="Aceti",
            username="acetimarco",
        )
        self.usr2 = TgUser.objects.create(
            id=244426552,
            first_name="Sette",
            last_name="Magic",
        )
        self.usr3 = TgUser.objects.create(
            id=108121631,
            first_name="Davide",
            last_name="Busolin",
            username="davidebusolin",
        )

        self.priv1 = UserPrivilege.objects.create(
            user=self.usr1,
            type=UserPrivilege.PrivilegeTypes.TUTOR,
            scope=UserPrivilege.PrivilegeScopes.GROUPS,
            custom_title="Tutor",
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=True,
            can_manage_chat=False,
            can_delete_messages=False,
            can_manage_voice_chats=False,
            can_restrict_members=False,
            can_promote_members=False,
        )
        self.priv1.authorized_groups.add(self.group1)
        self.priv1.save()

        self.priv2 = UserPrivilege.objects.create(
            user=self.usr1,
            type=UserPrivilege.PrivilegeTypes.ADMIN,
            scope=UserPrivilege.PrivilegeScopes.ALL,
            custom_title="C.A.N.",
            can_change_info=True,
            can_invite_users=True,
            can_pin_messages=True,
            can_manage_chat=True,
            can_delete_messages=True,
            can_manage_voice_chats=True,
            can_restrict_members=True,
            can_promote_members=True,
        )

        self.priv3 = UserPrivilege.objects.create(
            user=self.usr2,
            type=UserPrivilege.PrivilegeTypes.ADMIN,
            scope=UserPrivilege.PrivilegeScopes.DEGREES,
            custom_title="Administrator",
            can_change_info=True,
            can_invite_users=True,
            can_pin_messages=True,
            can_manage_chat=True,
            can_delete_messages=True,
            can_manage_voice_chats=True,
            can_restrict_members=True,
            can_promote_members=False,
        )
        self.priv3.authorized_degrees.add(deg1)
        self.priv3.save()

        self.priv4 = UserPrivilege.objects.create(
            user=self.usr3,
            type=UserPrivilege.PrivilegeTypes.REPRESENTATIVE,
            scope=UserPrivilege.PrivilegeScopes.DEPARTMENTS,
            custom_title="Representative",
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False,
            can_manage_chat=True,
            can_delete_messages=False,
            can_manage_voice_chats=False,
            can_restrict_members=False,
            can_promote_members=False,
        )
        self.priv4.authorized_departments.add(dip1)
        self.priv4.save()

    def test_privilege(self):
        # The most specific privilege is the one that should be returned
        self.assertEqual(self.usr1.get_privileges(self.group1), self.priv1)
        self.assertEqual(self.usr1.get_privileges(self.group2), self.priv2)
        self.assertEqual(self.usr1.get_privileges(self.group3), self.priv2)

        # self.usr2 is admin within the Computer Science degree, not Medicine
        self.assertEqual(self.usr2.get_privileges(self.group1), self.priv3)
        self.assertEqual(self.usr2.get_privileges(self.group2), self.priv3)
        self.assertEqual(self.usr2.get_privileges(self.group3), False)

        # self.usr3 is admin within the Computer Science degree, not Health
        self.assertEqual(self.usr3.get_privileges(self.group1), self.priv4)
        self.assertEqual(self.usr3.get_privileges(self.group2), self.priv4)
        self.assertEqual(self.usr3.get_privileges(self.group3), False)


class TelegramBotTestCase(TestCase):
    def setUp(self):
        self.maxDiff = None
        self.bot1 = TelegramBot.objects.create(
            token="123456789:cXoh8Mf3SHxvWD4eVThAhvjziny4xSZP8HQ",
            notes="This bot does not exists",
        )

        self.bot2 = TelegramBot.objects.create(
            token=TEST_BOT_TOKEN,
            notes="This bot should exist"
        )

    def test_censured_token(self):
        self.assertEqual(self.bot1.censured_token, "123456789:••••••••••••••••••••••••••••••ZP8HQ")

    def test_username(self):
        self.assertEqual(self.bot2.username, TEST_BOT_USERNAME)

    def test_str(self):
        self.assertEqual(str(self.bot2), f"{TEST_BOT_USERNAME}")

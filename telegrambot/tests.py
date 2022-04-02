import os
from unittest import skipIf

from django.test import TestCase
from rest_framework.renderers import JSONRenderer as Renderer

from telegrambot.models import (
    User as TgUser,
    Group as TgGroup,
    TelegramBot,
)
from telegrambot.serializers import (
    UserSerializer,
    GroupSerializer,
)

TEST_BOT_TOKEN = os.environ.get("TEST_BOT_TOKEN", None)
TEST_BOT_USERNAME = os.environ.get("TEST_BOT_USERNAME", None)


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


@skipIf(not (TEST_BOT_USERNAME and TEST_BOT_TOKEN), "The TEST_BOT_* environment variables are not set")
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

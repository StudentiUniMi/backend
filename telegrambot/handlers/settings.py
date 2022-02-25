import math
from django.db.models import QuerySet
from telegram import (
    Update,
    User,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from telegram.ext import CallbackContext
from typing import List, Tuple, Union

from telegrambot.handlers import welcome
from telegrambot.models import (
    User as DBUser,
)
from university.models import Degree


class DegreePaginator:
    """Inline keyboard markup paginator for degree"""

    def __init__(self, degree_type: str, items_per_page=5):
        self.degree_type = degree_type
        self.items_per_page = items_per_page
        self._data: QuerySet[Degree] = Degree.objects.filter(type=degree_type).order_by("name")

    @staticmethod
    def parse_callback_data(data: str) -> Union[Tuple[str, int], Tuple[None, None]]:
        """Parse raw callback data.
        Returns (None, None) if the user has selected the "skip" option, a tuple with degree type and page number otherwise.
        """
        info = data.split("@")[-1]
        if info == "SKIP":
            return None

        degree_type, page_number = info.split("|")
        return degree_type, int(page_number)

    @property
    def page_count(self) -> int:
        return math.ceil(self._data.count() / self.items_per_page)

    def _get_queryset_for_page(self, page: int) -> QuerySet[Degree]:
        start: int = page * self.items_per_page
        end: int = start + self.items_per_page
        return self._data[start:end]

    def markup(self, page: int) -> InlineKeyboardMarkup:
        buttons: List[List[InlineKeyboardButton]] = list()
        for degree in self._get_queryset_for_page(page):
            buttons.append([
                InlineKeyboardButton(
                    text=f"{degree.name}",
                    callback_data=f"set_degree@{degree.pk}"
                )
            ])

        controls: List[InlineKeyboardButton] = list()
        if page != 0:
            controls.append(
                InlineKeyboardButton(
                    text=f"⬅️",
                    callback_data=f"ask_degree@{self.degree_type}|{page - 1}"
                )
            )
        if page < self.page_count - 1:
            controls.append(
                InlineKeyboardButton(
                    text=f"➡️",
                    callback_data=f"ask_degree@{self.degree_type}|{page + 1}"
                )
            )
        buttons.append(controls)

        buttons.append([InlineKeyboardButton(
            text="🚫 Non studente / salta",
            callback_data="set_degree@SKIP"
        )])
        buttons.append([InlineKeyboardButton(
            text="🔙 Torna indietro",
            callback_data="ask_degree_type",
        )])
        return InlineKeyboardMarkup(buttons)


def ask_language(update: Update, _: CallbackContext):
    user_language = DBUser.objects.get(pk=update.effective_user.id).language

    update.callback_query.message.edit_text(
        # TODO: proper text
        text="Quale è la tua lingua?",
        parse_mode="html",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text=f"{'● ' if user_language == 'IT' else ''}🇮🇹 Italiano",
                    callback_data="set_language@IT",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"{'● ' if user_language == 'EN' else ''}🇬🇧 English",
                    callback_data="set_language@EN",
                ),
            ]
        ]),
    )


def set_language(update: Update, context: CallbackContext):
    callback_query: CallbackQuery = update.callback_query
    user: User = update.callback_query.from_user
    dbuser: DBUser = DBUser.objects.get(id=user.id)

    language: str = callback_query.data.split("@")[-1]
    dbuser.language = language
    dbuser.save()
    callback_query.answer("✅ Fatto!")

    if context.user_data.get("conversation") == "welcome":
        ask_gender(update, context)


def ask_gender(update: Update, _: CallbackContext):
    previous_state = "ask_language"
    user_gender = DBUser.objects.get(pk=update.effective_user.id).gender

    update.callback_query.message.edit_text(
        # TODO: proper text,
        text="Quale è il tuo genere?",
        parse_mode="html",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text=f"{'● ' if user_gender == 'M' else ''}👨 Maschio",
                    callback_data="set_gender@M",
                ),
                InlineKeyboardButton(
                    text=f"{'● ' if user_gender == 'F' else ''}👩 Femmina",
                    callback_data="set_gender@F",
                ),
                InlineKeyboardButton(
                    text=f"{'● ' if user_gender == 'O' else ''}🧑 Altro",
                    callback_data="set_gender@O",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❔ Preferisco non rispondere",
                    callback_data="set_gender@N",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Torna indietro",
                    callback_data=previous_state,
                ),
            ]
        ])
    )


def set_gender(update: Update, context: CallbackContext):
    callback_query: CallbackQuery = update.callback_query
    user: User = update.callback_query.from_user
    dbuser: DBUser = DBUser.objects.get(id=user.id)
    gender: str = callback_query.data.split("@")[-1]
    if gender != "N":
        callback_query.answer("✅ Fatto!")
        dbuser.gender = gender
        dbuser.save()
    else:
        callback_query.answer()

    if context.user_data.get("conversation") == "welcome":
        ask_degree_type(update, context)


def ask_degree_type(update: Update, _: CallbackContext):
    previous_state = "ask_gender"

    update.callback_query.message.edit_text(
        text="Che tipo di corso di laurea segui?",
        parse_mode="html",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text="3️⃣ Triennale",
                    callback_data="ask_degree@B|0",
                ),
                InlineKeyboardButton(
                    text="2️⃣ Magistrale",
                    callback_data="ask_degree@M|0",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="5️⃣ A ciclo unico",
                    callback_data="ask_degree@C|0",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🚫 Non studente / salta",
                    callback_data="set_degree@SKIP",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Torna indietro",
                    callback_data=previous_state,
                ),
            ]
        ])
    )


def ask_degree(update: Update, context: CallbackContext):
    callback_query: CallbackQuery = update.callback_query
    degree_type, page_number = DegreePaginator.parse_callback_data(callback_query.data)
    # Skip degree selection
    if degree_type is None:
        if context.user_data.get("conservation") == "welcome":
            welcome.ask_rules_acceptance(update, context)
        return

    paginator = DegreePaginator(degree_type, 5)

    callback_query.message.edit_text(
        text="Seleziona il tuo corso di laurea dall'elenco",
        parse_mode="html",
        reply_markup=paginator.markup(page_number),
    )


def set_degree(update: Update, context: CallbackContext):
    callback_query: CallbackQuery = update.callback_query
    user: User = update.callback_query.from_user
    dbuser: DBUser = DBUser.objects.get(id=user.id)
    degree_pk: str = callback_query.data.split("@")[-1]
    if degree_pk != "SKIP":
        degree_pk = int(degree_pk)
        dbuser.degree = Degree.objects.get(pk=degree_pk)
        dbuser.save()
    callback_query.answer("✅ Fatto!")

    if context.user_data.get("conversation") == "welcome":
        welcome.ask_rules_acceptance(update, context)

from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework.renderers import JSONRenderer as Renderer

from telegrambot.models import (
    Group as TgGroup,
    User as TgUser,
)
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
        u = User()
        u.username = "stud"
        u.password = "pbkdf2_sha256$260000$UJgmwSuMA4dMp72jVMgmkO$EATbgbI1R+WyXCAw53GpRBxyTsHzOl5EGNymJyv2/c4="
        u.save()

    def test_correct_entry(self):
        data = """
        [{"facolta": "SAA", "dipartimento": "Dipartimento di Scienze Agrarie e Ambientali - Produzione, Territorio, Agroenergia", "anno": "A.A. 2021/2022", "corso": "Agrotecnologie per l'ambiente e il territorio", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/agrotecnologie-lambiente-e-il-territorio", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "MV", "dipartimento": "", "anno": "A.A. 2021/2022", "corso": "Allevamento e benessere degli animali d'affezione", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/allevamento-e-benessere-degli-animali-daffezione", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "ST", "dipartimento": "", "anno": "A.A. 2021/2022", "corso": "Artificial Intelligence", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/artificial-intelligence", "tipo": "Laurea triennale", "lingua": "Inglese"}, {"facolta": "MC", "dipartimento": "Dipartimento di Scienze Biomediche per la Salute", "anno": "A.A. 2021/2022", "corso": "Assistenza sanitaria", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/assistenza-sanitaria", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "K", "dipartimento": "Dipartimento di Scienze Farmacologiche e Biomolecolari", "anno": "A.A. 2021/2022", "corso": "Biotecnologia", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/biotecnologia", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "MC", "dipartimento": "Dipartimento di Biotecnologie Mediche e Medicina Traslazionale", "anno": "A.A. 2021/2022", "corso": "Biotecnologie mediche", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/biotecnologie-mediche", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "ST", "dipartimento": "Dipartimento di Chimica", "anno": "A.A. 2021/2022", "corso": "Chimica", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/chimica", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "SF", "dipartimento": "Dipartimento di Scienze Farmaceutiche", "anno": "A.A. 2021/2022", "corso": "Chimica e tecnologia farmaceutiche a ciclo unico", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/chimica-e-tecnologia-farmaceutiche-ciclo-unico", "tipo": "Laurea magistrale a ciclo unico", "lingua": "Italiano"}, {"facolta": "ST", "dipartimento": "Dipartimento di Chimica", "anno": "A.A. 2021/2022", "corso": "Chimica industriale", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/chimica-industriale", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "SPES", "dipartimento": "Dipartimento di Scienze Sociali e Politiche", "anno": "A.A. 2021/2022", "corso": "Comunicazione e societ\u00e0 (CES)", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/comunicazione-e-societa-ces", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "MC", "dipartimento": "Dipartimento di Scienze della Salute", "anno": "A.A. 2021/2022", "corso": "Dietistica", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/dietistica", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "SPES", "dipartimento": "Dipartimento di Economia, Management e Metodi Quantitativi", "anno": "A.A. 2021/2022", "corso": "Economia e management (EMA)", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/economia-e-management-ema", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "MC", "dipartimento": "Dipartimento di Fisiopatologia Medico-Chirurgica e dei Trapianti", "anno": "A.A. 2021/2022", "corso": "Educazione professionale", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/educazione-professionale", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "SF", "dipartimento": "Dipartimento di Scienze Farmacologiche e Biomolecolari", "anno": "A.A. 2021/2022", "corso": "Farmacia ciclo unico", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/farmacia-ciclo-unico", "tipo": "Laurea magistrale a ciclo unico", "lingua": "Italiano"}, {"facolta": "SU", "dipartimento": "Dipartimento di Filosofia Piero Martinetti", "anno": "A.A. 2021/2022", "corso": "Filosofia", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/filosofia", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "ST", "dipartimento": "Dipartimento di Fisica Aldo Pontremoli", "anno": "A.A. 2021/2022", "corso": "Fisica", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/fisica", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "MC", "dipartimento": "Dipartimento di Scienze della Salute", "anno": "A.A. 2021/2022", "corso": "Fisioterapia", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/fisioterapia", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "G", "dipartimento": "Dipartimento di Diritto Privato e Storia del Diritto", "anno": "A.A. 2021/2022", "corso": "Giurisprudenza a ciclo unico", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/giurisprudenza-ciclo-unico", "tipo": "Laurea magistrale a ciclo unico", "lingua": "Italiano, Inglese"}, {"facolta": "MC", "dipartimento": "Dipartimento di Scienze Biomediche, Chirurgiche ed Odontoiatriche", "anno": "A.A. 2021/2022", "corso": "Igiene dentale", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/igiene-dentale", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "MC", "dipartimento": "Dipartimento di Scienze Biomediche per la Salute", "anno": "A.A. 2021/2022", "corso": "Infermieristica", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/infermieristica", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "MC", "dipartimento": "Dipartimento di Fisiopatologia Medico-Chirurgica e dei Trapianti", "anno": "A.A. 2021/2022", "corso": "Infermieristica pediatrica", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/infermieristica-pediatrica", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "ST", "dipartimento": "Dipartimento di Informatica Giovanni degli Antoni", "anno": "A.A. 2021/2022", "corso": "Informatica", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/informatica", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "ST", "dipartimento": "Dipartimento di Informatica Giovanni degli Antoni", "anno": "A.A. 2021/2022", "corso": "Informatica musicale", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/informatica-musicale", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "ST", "dipartimento": "Dipartimento di Informatica Giovanni degli Antoni", "anno": "A.A. 2021/2022", "corso": "Informatica per la comunicazione digitale", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/informatica-la-comunicazione-digitale", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "SPES", "dipartimento": "Department of International, Legal, Historical and Politcal Studies", "anno": "A.A. 2021/2022", "corso": "International Politics, Law and Economics (IPLE)", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/international-politics-law-and-economics-iple", "tipo": "Laurea triennale", "lingua": "Inglese"}, {"facolta": "SU", "dipartimento": "Dipartimento di Studi Letterari, Filologici e Linguistici", "anno": "A.A. 2021/2022", "corso": "Lettere", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/lettere", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "SU", "dipartimento": "Dipartimento di Lingue e Letterature Straniere", "anno": "A.A. 2021/2022", "corso": "Lingue e letterature straniere", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/lingue-e-letterature-straniere", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "MC", "dipartimento": "Dipartimento di Scienze Biomediche e Cliniche L. Sacco", "anno": "A.A. 2021/2022", "corso": "Logopedia", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/logopedia", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "SPES", "dipartimento": "Dipartimento di Scienze Sociali e Politiche", "anno": "A.A. 2021/2022", "corso": "Management delle organizzazioni e del lavoro (MOL)", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/management-delle-organizzazioni-e-del-lavoro-mol", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "SPES", "dipartimento": "Dipartimento di Economia, Management e Metodi Quantitativi", "anno": "A.A. 2021/2022", "corso": "Management pubblico e della sanit\u00e0 (MAPS)", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/management-pubblico-e-della-sanita-maps", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "ST", "dipartimento": "Dipartimento di Matematica Federigo Enriques", "anno": "A.A. 2021/2022", "corso": "Matematica (triennale)", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/matematica-triennale", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "SMLC", "dipartimento": "Dipartimento di Scienze della Mediazione Linguistica e di Studi Interculturali", "anno": "A.A. 2021/2022", "corso": "Mediazione linguistica e culturale applicata all'ambito economico, giuridico e sociale (MED)", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/mediazione-linguistica-e-culturale-applicata-allambito-economico-giuridico-e-sociale-med", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "MC", "dipartimento": "Dipartimento di Scienze della Salute", "anno": "A.A. 2021/2022", "corso": "Medicina e chirurgia  - Polo San Paolo", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/medicina-e-chirurgia-polo-san-paolo", "tipo": "Laurea magistrale a ciclo unico", "lingua": "Italiano"}, {"facolta": "MC", "dipartimento": "Department of Medical Biotechnology and Translational Medicine", "anno": "A.A. 2021/2022", "corso": "Medicina e chirurgia - International Medical School", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/medicina-e-chirurgia-international-medical-school", "tipo": "Laurea magistrale a ciclo unico", "lingua": "Inglese"}, {"facolta": "MC", "dipartimento": "Dipartimento di Scienze Cliniche e di Comunit\u00e0", "anno": "A.A. 2021/2022", "corso": "Medicina e chirurgia - Polo Centrale", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/medicina-e-chirurgia-polo-centrale", "tipo": "Laurea magistrale a ciclo unico", "lingua": "Italiano"}, {"facolta": "MC", "dipartimento": "Dipartimento di Scienze Biomediche e Cliniche L. Sacco", "anno": "A.A. 2021/2022", "corso": "Medicina e chirurgia - Polo Vialba", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/medicina-e-chirurgia-polo-vialba", "tipo": "Laurea magistrale a ciclo unico", "lingua": "Italiano"}, {"facolta": "MV", "dipartimento": "Dipartimento di Medicina Veterinaria", "anno": "A.A. 2021/2022", "corso": "Medicina veterinaria a ciclo unico", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/medicina-veterinaria-ciclo-unico", "tipo": "Laurea magistrale a ciclo unico", "lingua": "Italiano"}, {"facolta": "MC", "dipartimento": "Dipartimento di Scienze Biomediche, Chirurgiche ed Odontoiatriche", "anno": "A.A. 2021/2022", "corso": "Odontoiatria e protesi dentaria", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/odontoiatria-e-protesi-dentaria", "tipo": "Laurea magistrale a ciclo unico", "lingua": "Italiano"}, {"facolta": "MC", "dipartimento": "Dipartimento di Scienze Cliniche e di Comunit\u00e0", "anno": "A.A. 2021/2022", "corso": "Ortottica ed assistenza oftalmologica", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/ortottica-ed-assistenza-oftalmologica", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "MC", "dipartimento": "Dipartimento di Scienze Cliniche e di Comunit\u00e0", "anno": "A.A. 2021/2022", "corso": "Ostetricia", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/ostetricia", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "MC", "dipartimento": "Dipartimento di Scienze Biomediche, Chirurgiche ed Odontoiatriche", "anno": "A.A. 2021/2022", "corso": "Podologia", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/podologia", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "SAA", "dipartimento": "Dipartimento di Scienze Agrarie e Ambientali - Produzione, Territorio, Agroenergia", "anno": "A.A. 2021/2022", "corso": "Produzione e protezione delle piante e dei sistemi del verde", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/produzione-e-protezione-delle-piante-e-dei-sistemi-del-verde", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "ST", "dipartimento": "Dipartimento di Bioscienze", "anno": "A.A. 2021/2022", "corso": "Scienze biologiche", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/scienze-biologiche", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "SU", "dipartimento": "Dipartimento di Beni Culturali e Ambientali", "anno": "A.A. 2021/2022", "corso": "Scienze dei beni culturali", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/scienze-dei-beni-culturali", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "G", "dipartimento": "Dipartimento di Scienze Giuridiche Cesare Beccaria", "anno": "A.A. 2021/2022", "corso": "Scienze dei servizi giuridici", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/scienze-dei-servizi-giuridici", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "MV", "dipartimento": "Dipartimento di Medicina Veterinaria", "anno": "A.A. 2021/2022", "corso": "Scienze delle produzioni animali ", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/scienze-delle-produzioni-animali", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "ST", "dipartimento": "Dipartimento di Scienze e Politiche Ambientali", "anno": "A.A. 2021/2022", "corso": "Scienze e politiche ambientali", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/scienze-e-politiche-ambientali", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "SF", "dipartimento": "Dipartimento di Scienze Farmacologiche e Biomolecolari", "anno": "A.A. 2021/2022", "corso": "Scienze e sicurezza chimico-tossicologiche dell'ambiente", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/scienze-e-sicurezza-chimico-tossicologiche-dellambiente", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "SAA", "dipartimento": "", "anno": "A.A. 2021/2022", "corso": "Scienze e tecnologie agrarie", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/scienze-e-tecnologie-agrarie", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "SAA", "dipartimento": "Dipartimento di Scienze per gli Alimenti, la Nutrizione e l'Ambiente", "anno": "A.A. 2021/2022", "corso": "Scienze e tecnologie alimentari ", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/scienze-e-tecnologie-alimentari", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "SAA", "dipartimento": "Dipartimento di Scienze per gli Alimenti, la Nutrizione e l'Ambiente", "anno": "A.A. 2021/2022", "corso": "Scienze e tecnologie della ristorazione", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/scienze-e-tecnologie-della-ristorazione", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "SF", "dipartimento": "Dipartimento di Scienze Farmaceutiche", "anno": "A.A. 2021/2022", "corso": "Scienze e tecnologie erboristiche ", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/scienze-e-tecnologie-erboristiche", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "ST", "dipartimento": "Dipartimento di Scienze della Terra Ardito Desio", "anno": "A.A. 2021/2022", "corso": "Scienze e tecnologie per lo studio e la conservazione dei beni culturali e dei supporti della informazione", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/scienze-e-tecnologie-lo-studio-e-la-conservazione-dei-beni-culturali-e-dei-supporti-della", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "ST", "dipartimento": "Dipartimento di Scienze della Terra Ardito Desio", "anno": "A.A. 2021/2022", "corso": "Scienze geologiche", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/scienze-geologiche", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "SPES", "dipartimento": "Dipartimento di Studi Internazionali, Giuridici e Storico-Politici", "anno": "A.A. 2021/2022", "corso": "Scienze internazionali e istituzioni europee (SIE)", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/scienze-internazionali-e-istituzioni-europee-sie", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "SM", "dipartimento": "Dipartimento di Scienze Biomediche per la Salute", "anno": "A.A. 2021/2022", "corso": "Scienze motorie, sport e salute", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/scienze-motorie-sport-e-salute", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "ST", "dipartimento": "Dipartimento di Scienze della Terra Ardito Desio", "anno": "A.A. 2021/2022", "corso": "Scienze naturali", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/scienze-naturali", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "SPES", "dipartimento": "Dipartimento di Scienze Sociali e Politiche", "anno": "A.A. 2021/2022", "corso": "Scienze politiche (SPO)", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/scienze-politiche-spo", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "SPES", "dipartimento": "Dipartimento di Scienze Sociali e Politiche", "anno": "A.A. 2021/2022", "corso": "Scienze sociali per la globalizzazione (GLO)", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/scienze-sociali-la-globalizzazione-glo", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "SU", "dipartimento": "Dipartimento di Beni Culturali e Ambientali", "anno": "A.A. 2021/2022", "corso": "Scienze umane dell'ambiente, del territorio e del paesaggio", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/scienze-umane-dellambiente-del-territorio-e-del-paesaggio", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "SU", "dipartimento": "Dipartimento di Studi Storici", "anno": "A.A. 2021/2022", "corso": "Scienze umanistiche per la comunicazione", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/scienze-umanistiche-la-comunicazione", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "ST", "dipartimento": "Dipartimento di Informatica Giovanni degli Antoni", "anno": "A.A. 2021/2022", "corso": "Sicurezza dei sistemi e delle reti informatiche", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/sicurezza-dei-sistemi-e-delle-reti-informatiche", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "ST", "dipartimento": "Dipartimento di Informatica Giovanni degli Antoni", "anno": "A.A. 2021/2022", "corso": "Sicurezza dei sistemi e delle reti informatiche online", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/sicurezza-dei-sistemi-e-delle-reti-informatiche-online", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "SU", "dipartimento": "Dipartimento di Studi Storici", "anno": "A.A. 2021/2022", "corso": "Storia", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/storia", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "MC", "dipartimento": "Dipartimento di Scienze Biomediche e Cliniche L. Sacco", "anno": "A.A. 2021/2022", "corso": "Tecnica della riabilitazione psichiatrica", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/tecnica-della-riabilitazione-psichiatrica", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "MC", "dipartimento": "Dipartimento di Scienze Cliniche e di Comunit\u00e0", "anno": "A.A. 2021/2022", "corso": "Tecniche audiometriche ", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/tecniche-audiometriche", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "MC", "dipartimento": "Dipartimento di Scienze Cliniche e di Comunit\u00e0", "anno": "A.A. 2021/2022", "corso": "Tecniche audioprotesiche", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/tecniche-audioprotesiche", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "MC", "dipartimento": "Dipartimento di Scienze Biomediche per la Salute", "anno": "A.A. 2021/2022", "corso": "Tecniche della prevenzione nell'ambiente e nei luoghi di lavoro", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/tecniche-della-prevenzione-nellambiente-e-nei-luoghi-di-lavoro", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "MC", "dipartimento": "Dipartimento di Scienze Biomediche, Chirurgiche ed Odontoiatriche", "anno": "A.A. 2021/2022", "corso": "Tecniche di fisiopatologia cardiocircolatoria e perfusione cardiovascolare", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/tecniche-di-fisiopatologia-cardiocircolatoria-e-perfusione-cardiovascolare", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "MC", "dipartimento": "Dipartimento di Scienze Biomediche per la Salute", "anno": "A.A. 2021/2022", "corso": "Tecniche di laboratorio biomedico", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/tecniche-di-laboratorio-biomedico", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "MC", "dipartimento": "Dipartimento di Scienze della Salute", "anno": "A.A. 2021/2022", "corso": "Tecniche di neurofisiopatologia ", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/tecniche-di-neurofisiopatologia", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "MC", "dipartimento": "Dipartimento di Oncologia ed Emato-Oncologia", "anno": "A.A. 2021/2022", "corso": "Tecniche di radiologia medica, per immagini e radioterapia", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/tecniche-di-radiologia-medica-immagini-e-radioterapia", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "MC", "dipartimento": "Dipartimento di Scienze Biomediche, Chirurgiche ed Odontoiatriche", "anno": "A.A. 2021/2022", "corso": "Tecniche ortopediche", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/tecniche-ortopediche", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "MC", "dipartimento": "Dipartimento di Scienze Biomediche e Cliniche L. Sacco", "anno": "A.A. 2021/2022", "corso": "Terapia della neuro e psicomotricit\u00e0 dell'et\u00e0 evolutiva", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/terapia-della-neuro-e-psicomotricita-delleta-evolutiva", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "MC", "dipartimento": "Dipartimento di Scienze della Salute", "anno": "A.A. 2021/2022", "corso": "Terapia occupazionale", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/terapia-occupazionale", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "SAA", "dipartimento": "Dipartimento di Scienze Agrarie e Ambientali - Produzione, Territorio, Agroenergia", "anno": "A.A. 2021/2022", "corso": "Valorizzazione e tutela dell'ambiente e del territorio montano", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/valorizzazione-e-tutela-dellambiente-e-del-territorio-montano", "tipo": "Laurea triennale", "lingua": "Italiano"}, {"facolta": "SAA", "dipartimento": "Dipartimento di Scienze Agrarie e Ambientali - Produzione, Territorio, Agroenergia", "anno": "A.A. 2021/2022", "corso": "Viticoltura ed enologia", "sito": "https://unimi.it/it/corsi/corsi-di-laurea/viticoltura-ed-enologia", "tipo": "Laurea triennale", "lingua": "Italiano"}]
        """
        c = Client()
        c.login(username="stud", password="stud")
        resp = c.post("/parse-json-data", {"json_data": data})
        self.assertEqual(resp.content, b'Data has been added succesfully!')

    def test_malformed_json(self):
        data = """
        asd
        """
        c = Client()
        c.login(username="stud", password="stud")
        resp = c.post("/parse-json-data", {"json_data": data})
        self.assertEqual(resp.content, b'The data that was provided is not a well-formed JSON object!')

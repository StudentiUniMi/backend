from django.contrib import admin
from django.db import models

from telegrambot.models import (
    User as TgUser,
    Group as TgGroup,
)

DEGREE_TYPES = (
    ('B', "Triennale"),
    ('M', "Magistrale"),
    ('C', "Laurea a ciclo unico")
)


class Department(models.Model):
    """An university department.

    Example: Computer Science Department "Giovanni degli Antoni"
    """
    name = models.CharField("name", max_length=128, unique=True)

    def __str__(self) -> str:
        return self.name


class Representative(models.Model):
    """An university representative.
    Mainly used to show contact information on the website.

    Example: Giulio Lucani
    """
    class Meta:
        verbose_name = "Representative"
        verbose_name_plural = "Representatives"

    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="representatives")
    tguser = models.ForeignKey(TgUser, on_delete=models.CASCADE, related_name="representative")
    title = models.CharField("title", max_length=64)

    def __str__(self) -> str:
        return f"{str(self.tguser)}, {self.title} ({self.department.name})"


class Degree(models.Model):
    """An university degree.

    Example: Bachelor of Computer Science
    """
    class Meta:
        verbose_name = "Degree"
        verbose_name_plural = "Degrees"
        unique_together = ("name", "type")

    name = models.CharField("name", max_length=128)
    type = models.CharField("degree type", max_length=1, choices=DEGREE_TYPES)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="degrees")
    slug = models.CharField("slug", max_length=64, default="default_slug")  # the default is needed for migrations

    def __str__(self) -> str:
        return f"{self.name} [{''.join([t[1] if t[0] == self.type else '' for t in DEGREE_TYPES])}]"  # hacky shit


class Course(models.Model):
    """An university course.

    Example: Programming I
    """

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    group = models.ForeignKey(TgGroup, on_delete=models.SET_NULL, related_name="courses", blank=True, null=True)
    degrees = models.ManyToManyField(Degree, through="CourseDegree", related_name="courses")
    name = models.CharField("name", max_length=128)
    cfu = models.PositiveSmallIntegerField("CFUs")
    wiki_link = models.CharField("wiki link", max_length=128, blank=True, null=True)

    @property
    @admin.display(
        ordering='name',
        description='Degrees',
    )
    def str_degrees(self) -> str:
        """Return a comma-separated list of linked degrees"""
        return ', '.join([d.name for d in self.degrees.all()])

    def __str__(self) -> str:
        return f"{self.name} ({self.str_degrees})"


class CourseDegree(models.Model):
    """The relation between a course and a degree.

    Example: Programming I is offered the 1st semester of the 1st year of the Computer Science degree
    """
    # https://docs.djangoproject.com/en/3.2/topics/db/models/#extra-fields-on-many-to-many-relationships
    degree = models.ForeignKey(Degree, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    year = models.PositiveSmallIntegerField("year", default=0)          # 0 = no year assigned (e.g. optional course)
    semester = models.PositiveSmallIntegerField("semester", default=0)  # 0 = no semester assigned

    def __str__(self):
        return f"{self.course.name} ∈ {self.degree.name}"


class CourseLink(models.Model):
    """Additional links to show on the website for a specific course."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="links")
    name = models.CharField("link name", max_length=32)
    url = models.URLField("link URL")

    def __str__(self):
        return f"{str(self.course)} - {self.name}"

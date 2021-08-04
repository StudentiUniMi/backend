from django.contrib import admin
from django.db import models

from telegram.models import Group as TgGroup

DEGREE_TYPES = (
    ('B', "Triennale"),
    ('M', "Magistrale"),
    ('C', "Laurea a ciclo unico")
)


class Department(models.Model):
    name = models.CharField("name", max_length=64)

    def __str__(self):
        return self.name


class Degree(models.Model):
    class Meta:
        verbose_name = "Degree"
        verbose_name_plural = "Degrees"

    name = models.CharField("name", max_length=128)
    type = models.CharField("degree type", max_length=1, choices=DEGREE_TYPES)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="degrees")
    slug = models.CharField("slug", max_length=64, default="default_slug")  # the default is needed for migrations

    def __str__(self):
        return f"{self.name} [{''.join([t[1] if t[0] == self.type else '' for t in DEGREE_TYPES])}]"  # hacky shit


class Course(models.Model):
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
    def str_degrees(self):
        return ', '.join([d.name for d in self.degrees.all()])

    def __str__(self):
        return f"{self.name} ({self.str_degrees})"


class CourseDegree(models.Model):
    # https://docs.djangoproject.com/en/3.2/topics/db/models/#extra-fields-on-many-to-many-relationships
    degree = models.ForeignKey(Degree, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    year = models.PositiveSmallIntegerField("year", default=0)          # 0 = no year assigned (e.g. optional course)
    semester = models.PositiveSmallIntegerField("semester", default=0)  # 0 = no semester assigned

    def __str__(self):
        return f"{self.course.name} ∈ {self.degree.name}"


class CourseLink(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="links")
    name = models.CharField("link name", max_length=32)
    url = models.URLField("link URL")

    def __str__(self):
        return f"{str(self.course)} - {self.name}"

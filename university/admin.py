from django.contrib import admin

from university.models import (
    Department,
    Degree,
    Course,
    CourseDegree,
    CourseLink,
    DEGREE_TYPES,
)


class CourseDegreeInline(admin.TabularInline):
    model = CourseDegree
    extra = 1


class CourseLinkInline(admin.TabularInline):
    model = CourseLink
    extra = 1


class DegreeTypeFilter(admin.SimpleListFilter):
    title = "degree type"
    parameter_name = "degree_type"

    def lookups(self, request, model_admin):
        return DEGREE_TYPES

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(type=self.value())


class CourseDegreeNameFilter(admin.SimpleListFilter):
    title = "degree name"
    parameter_name = "degree_name"

    def lookups(self, request, model_admin):
        degrees = Degree.objects.all()
        return (
            (d.pk, d.name) for d in degrees
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(degree__in=self.value())


class CourseDegreeTypeFilter(admin.SimpleListFilter):
    title = "degree type"
    parameter_name = "degree_type"

    def lookups(self, request, model_admin):
        return DEGREE_TYPES

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        matched_degrees = Degree.objects.filter(type=self.value())
        return queryset.filter(degrees__in=matched_degrees).distinct()


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    search_fields = ("name", )


@admin.register(Degree)
class DegreeAdmin(admin.ModelAdmin):
    list_filter = (DegreeTypeFilter, )
    search_fields = ("name", "department", )
    fields = ("name", "type", "department", "slug", )
    inlines = (CourseDegreeInline, )


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "cfu", "str_degrees", )
    list_filter = (CourseDegreeNameFilter, CourseDegreeTypeFilter, )
    search_fields = ("name", )
    fields = ("name", "cfu", "group", "wiki_link", )
    inlines = (CourseDegreeInline, CourseLinkInline, )

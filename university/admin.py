from django.contrib import admin

from university.models import (
    Representative,
    Professor,
    Department,
    Degree,
    Course,
    CourseDegree,
    CourseLink,
    DEGREE_TYPES,
)


class RepresentativeInline(admin.TabularInline):
    model = Representative
    extra = 1
    autocomplete_fields = ("tguser", )


class CourseDegreeInline(admin.TabularInline):
    model = CourseDegree
    extra = 1
    autocomplete_fields = ("course", "degree", )


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
    parameter_name = "degree_id"

    def lookups(self, request, model_admin):
        degrees = Degree.objects.all()
        return (
            (d.pk, d.name) for d in degrees
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(degrees__in=self.value())


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


@admin.register(Representative)
class RepresentativeAdmin(admin.ModelAdmin):
    list_display = ("tguser", "department", "degree_name", )
    list_editable = ("degree_name", )
    search_fields = ("tguser__first_name", "tguser__last_name", "tguser__username", )
    fields = ("department", "tguser", "degree_name", )
    autocomplete_fields = ("department", "tguser", )


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ("__str__", )
    search_fields = ("first_name", "last_name", )

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    search_fields = ("name", )
    fields = ("name", "slug", "icon", )
    inlines = (RepresentativeInline, )


@admin.register(Degree)
class DegreeAdmin(admin.ModelAdmin):
    list_filter = (DegreeTypeFilter, )
    search_fields = ("name", "type", )
    fields = ("name", "type", "department", "slug", "icon", "group", )
    autocomplete_fields = ("department", "group", )
    inlines = (CourseDegreeInline, )


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "cfu", "str_degrees", "professor", )
    list_filter = (CourseDegreeNameFilter, CourseDegreeTypeFilter, )
    search_fields = ("name", )
    fields = ("name", "cfu", "professor", "group", "wiki_link", "slug_unimi")
    autocomplete_fields = ("professor", "group", )
    readonly_fields = ("slug_unimi", )
    inlines = (CourseDegreeInline, CourseLinkInline, )

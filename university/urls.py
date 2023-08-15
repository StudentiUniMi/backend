from django.urls import path

import university.views
from university import views


urlpatterns = [
    path("import/degrees", university.views.import_degrees, name="import-degrees"),
    path("import/courses", university.views.import_courses, name="import-courses"),
    path(r"departments", views.DepartmentViewSet.as_view({"get": "list"}), name="api-departments"),
    path(r"degrees", views.degrees_by_department, name="api-degrees"),
    path(r"degree", views.degree_by_slug_or_pk, name="api-degree"),
    path(r"search-degrees", views.degrees_by_query, name="api-search-degrees"),
    path(r"courses", views.courses_by_degree, name="api-courses"),
    path(r"representatives", views.representatives_by_department, name="api-representatives"),
    path(r"typing-degrees", views.typing_degrees, name="api-typing-degrees"),
    path(r"admins", views.admin_by_degree, name="admins-by-degree"),
    path(r"extra-groups", views.extra_groups, name="extra-groups"),
]

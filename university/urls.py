from django.urls import path

from university import views


urlpatterns = [
    path(r"departments", views.DepartmentViewSet.as_view({"get": "list"}), name="api-departments"),
    path(r"degrees", views.degrees_by_department, name="api-degrees"),
    path(r"courses", views.courses_by_degree, name="api-courses"),
    path(r"representatives", views.representatives_by_department, name="api-representatives"),
]

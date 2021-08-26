from django.urls import include, path
from rest_framework import routers

import university.views
from university import views

router = routers.DefaultRouter()
router.register(r"degrees", views.DegreeViewSet, basename="Degree")
router.register(r"departments", views.DepartmentViewSet, basename="Department")


urlpatterns = [
    path('', include(router.urls)),
    path("import/degrees", university.views.import_degrees, name="import-degrees"),
    path("import/courses", university.views.import_courses, name="import-courses")
]

from django.urls import include, path
from rest_framework import routers

import university.views
from university import views

router = routers.DefaultRouter()
router.register(r"degrees", views.DegreeViewSet, basename="Degree")
router.register(r"departments", views.DepartmentViewSet, basename="Department")


urlpatterns = [
    path('', include(router.urls)),
    path('degrees', university.views.parse_degrees, name="parse-degrees"),
    path('courses', university.views.parse_courses, name="parse-courses")
]

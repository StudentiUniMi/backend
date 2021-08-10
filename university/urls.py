from django.urls import include, path
from rest_framework import routers

from university import views

router = routers.DefaultRouter()
router.register(r"degrees", views.DegreeViewSet, basename="Degree")
router.register(r"departments", views.DepartmentViewSet, basename="Department")


urlpatterns = [
    path('', include(router.urls)),
]

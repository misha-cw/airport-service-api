from django.urls import path, include
from rest_framework import routers

from airport.views import AirportViewSet, CrewViewSet


router = routers.DefaultRouter()
router.register(r"airports", AirportViewSet)
router.register(r"crews", CrewViewSet)

urlpatterns = [
    path("", include(router.urls)),
]

app_name = "airport"

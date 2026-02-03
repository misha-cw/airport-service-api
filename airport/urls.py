from django.urls import path, include
from rest_framework import routers

from airport.views import AirplaneTypeViewSet, AirportViewSet, CrewViewSet


router = routers.DefaultRouter()
router.register("airports", AirportViewSet)
router.register("crews", CrewViewSet)
router.register("airplane_types", AirplaneTypeViewSet)

urlpatterns = [
    path("", include(router.urls)),
]

app_name = "airport"

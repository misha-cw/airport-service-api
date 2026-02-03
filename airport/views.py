from rest_framework import viewsets

from airport.models import AirplaneType, Airport, Crew
from airport.serializers import (
    AirplaneTypeSerializer,
    AirportSerializer,
    CrewSerializer,
)


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer


class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer

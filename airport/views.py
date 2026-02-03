from rest_framework import viewsets

from airport.models import Airport
from airport.serializers import AirportSerializer


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer

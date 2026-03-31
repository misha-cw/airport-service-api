from rest_framework import status
from rest_framework.test import APIClient
from django.test import TestCase
from django.urls import reverse
from django.db.models import F, Count

from airport.models import Flight
from airport.serializers import (
    FlightListSerializer,
    FlightDetailSerializer,
)
from airport.tests.utils import (
    sample_airplane,
    sample_crew,
    sample_flight,
    sample_route,
    USER,
)

FLIGHT_URL = reverse("airport:flight-list")


def detail_url(flight_id):
    return reverse("airport:flight-detail", args=[flight_id])


class UnauthenticatedFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(FLIGHT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = USER.objects.create_user(
            email="test@example.com", password="testpassword123"
        )
        self.client.force_authenticate(user=self.user)

    def test_list_flights(self):
        route = sample_route()
        sample_flight(route=route, departure_time="2024-01-02T10:00:00Z")
        sample_flight(route=route)

        res = self.client.get(FLIGHT_URL)
        flights = Flight.objects.annotate(
            tickets_available=F("airplane__rows") * F("airplane__seats_in_row")
            - Count("tickets")
        )
        serializer = FlightListSerializer(flights, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_flight(self):
        flight = sample_flight()
        url = detail_url(flight.id)
        res = self.client.get(url)

        serializer = FlightDetailSerializer(flight)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_flight_forbidden(self):
        route = sample_route()
        airplane = sample_airplane()
        crew = sample_crew()

        payload = {
            "route": route.id,
            "airplane": airplane.id,
            "crew": [crew.id],
            "departure_time": "2024-01-01T10:00:00Z",
            "arrival_time": "2024-01-01T12:00:00Z",
        }

        res = self.client.post(FLIGHT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_filtering_flight_by_route_id(self):
        flight1 = sample_flight()
        flight2 = sample_flight()

        res = self.client.get(FLIGHT_URL, {"route": flight1.route.id})

        flights = Flight.objects.annotate(
            tickets_available=F("airplane__rows") * F("airplane__seats_in_row")
            - Count("tickets")
        )

        flight1 = flights.get(id=flight1.id)
        flight2 = flights.get(id=flight2.id)

        serializer1 = FlightListSerializer(flight1)
        serializer2 = FlightListSerializer(flight2)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_filtering_flight_by_departure_time(self):
        flight1 = sample_flight(departure_time="2024-01-02T10:00:00Z")
        flight2 = sample_flight(departure_time="2024-01-01T10:00:00Z")

        res = self.client.get(FLIGHT_URL, {"departure_time": "2024-01-02"})

        flights = Flight.objects.annotate(
            tickets_available=F("airplane__rows") * F("airplane__seats_in_row")
            - Count("tickets")
        )

        flight1 = flights.get(id=flight1.id)
        flight2 = flights.get(id=flight2.id)

        serializer1 = FlightListSerializer(flight1)
        serializer2 = FlightListSerializer(flight2)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)


class AdminFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = USER.objects.create_superuser(
            email="admin@example.com", password="adminpassword123", is_staff=True
        )
        self.client.force_authenticate(user=self.user)

    def test_create_flight(self):
        payload = {
            "route": sample_route().id,
            "airplane": sample_airplane().id,
            "crew": [
                sample_crew(first_name="Rick").id,
                sample_crew(first_name="John").id,
            ],
            "departure_time": "2024-01-01T10:00:00Z",
            "arrival_time": "2024-01-01T12:00:00Z",
        }

        res = self.client.post(FLIGHT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        flight = Flight.objects.get(id=res.data["id"])

        for key in ["route", "airplane"]:
            self.assertEqual(getattr(flight, key).id, payload[key])

        for key in ["departure_time", "arrival_time"]:
            self.assertEqual(
                getattr(flight, key).isoformat().replace("+00:00", "Z"), payload[key]
            )

        crew_ids = set(flight.crew.values_list("id", flat=True))
        self.assertEqual(crew_ids, set(payload["crew"]))

    def test_put_flight_not_allowed(self):
        flight = sample_flight()
        payload = {
            "route": sample_route().id,
            "airplane": sample_airplane().id,
            "crew": [
                sample_crew(first_name="Rick").id,
                sample_crew(first_name="John").id,
            ],
            "departure_time": "2024-01-01T12:00:00Z",
            "arrival_time": "2024-01-01T14:00:00Z",
        }
        url = detail_url(flight.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_flight_not_allowed(self):
        flight = sample_flight()
        res = self.client.delete(detail_url(flight.id))

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

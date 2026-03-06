from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from airport.models import Airplane, AirplaneType
from airport.serializers import (
    AirplaneDetailSerializer,
    AirplaneListSerializer,
)

AIRPLANE_URL = reverse("airport:airplane-list")


def detail_url(airplane_id):
    return reverse("airport:airplane-detail", args=[airplane_id])


def sample_airplane_type(**params):
    defaults = {
        "name": "Sample Airplane Type",
    }
    defaults.update(params)
    return AirplaneType.objects.create(**defaults)


def sample_airplane(**params) -> Airplane:
    defaults = {
        "name": "Sample Airplane",
        "rows": 10,
        "seats_in_row": 6,
        "airplane_type": None,
        "image": None,
    }
    defaults.update(params)
    return Airplane.objects.create(**defaults)


class UnauthenticatedAirplaneApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(AIRPLANE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirplaneApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@example.com", password="testpassword123"
        )
        self.client.force_authenticate(user=self.user)

    def test_list_airplanes(self):
        airplane_type = sample_airplane_type()
        sample_airplane(name="Airplane 1", airplane_type=airplane_type)
        sample_airplane(name="Airplane 2", airplane_type=airplane_type)

        res = self.client.get(AIRPLANE_URL)
        airplanes = Airplane.objects.all().order_by("id")
        serializer = AirplaneListSerializer(airplanes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_airplane_forbidden(self):
        airplane_type = sample_airplane_type()
        payload = {
            "name": "New Airplane",
            "airplane_type": airplane_type.id,
        }
        res = self.client.post(AIRPLANE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_airplane(self):
        airplane_type = sample_airplane_type()
        airplane = sample_airplane(name="Airplane 1", airplane_type=airplane_type)

        url = detail_url(airplane.id)
        res = self.client.get(url)

        serializer = AirplaneDetailSerializer(airplane)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


class AdminAirplaneApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = get_user_model().objects.create_superuser(
            email="admin@example.com", password="adminpassword123", is_staff=True
        )
        self.client.force_authenticate(user=self.admin_user)

    def test_create_airplane(self):
        airplane_type = sample_airplane_type()
        payload = {
            "name": "New Airplane",
            "rows": 20,
            "seats_in_row": 8,
            "airplane_type": airplane_type.id,
        }
        res = self.client.post(AIRPLANE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Airplane.objects.count(), 1)
        airplane = Airplane.objects.get(id=res.data["id"])
        for key in payload:
            attr = getattr(airplane, key)
            if hasattr(attr, "id"):
                attr = attr.id

            self.assertEqual(attr, payload[key])

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from airport.models import AirplaneType
from airport.serializers import AirplaneTypeSerializer

AIRPLANE_TYPE_URL = reverse("airport:airplanetype-list")


def sample_airplane_type(**params) -> AirplaneType:
    defaults = {
        "name": "Test Airplane Type",
    }
    defaults.update(params)
    return AirplaneType.objects.create(**defaults)


class UnauthenticatedAirplaneTypeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(AIRPLANE_TYPE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirplaneTypeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@example.com", password="testpassword123"
        )
        self.client.force_authenticate(user=self.user)

    def test_list_airplane_types(self):
        sample_airplane_type(name="Airplane Type 1")
        sample_airplane_type(name="Airplane Type 2")

        res = self.client.get(AIRPLANE_TYPE_URL)
        airplane_types = AirplaneType.objects.all()
        serializer = AirplaneTypeSerializer(airplane_types, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_airplane_type_forbidden(self):
        payload = {"name": "New Airplane Type"}
        res = self.client.post(AIRPLANE_TYPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminAirplaneTypeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = get_user_model().objects.create_superuser(
            email="admin@example.com", password="adminpassword123", is_staff=True
        )
        self.client.force_authenticate(user=self.admin_user)

    def test_create_airplane_type(self):
        payload = {"name": "New Airplane Type"}
        res = self.client.post(AIRPLANE_TYPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AirplaneType.objects.count(), 1)
        airplane_type = AirplaneType.objects.get(id=res.data["id"])
        self.assertEqual(airplane_type.name, payload["name"])

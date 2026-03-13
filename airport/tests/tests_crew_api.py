from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from airport.models import Crew
from airport.serializers import CrewSerializer
from airport.tests.utils import sample_crew

CREW_URL = reverse("airport:crew-list")


class UnauthenticatedCrewApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(CREW_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedCrewApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@example.com", password="testpassword123"
        )
        self.client.force_authenticate(user=self.user)

    def test_list_crews(self):
        sample_crew(first_name="Crew 1", last_name="Last Name 1")
        sample_crew(first_name="Crew 2", last_name="Last Name 2")

        res = self.client.get(CREW_URL)
        crews = Crew.objects.all().order_by("id")
        serializer = CrewSerializer(crews, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_crew_forbidden(self):
        payload = {
            "first_name": "New First Name",
            "last_name": "New Last Name",
        }
        res = self.client.post(CREW_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminCrewApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = get_user_model().objects.create_superuser(
            email="admin@example.com", password="adminpassword123", is_staff=True
        )
        self.client.force_authenticate(user=self.admin_user)

    def test_create_crew(self):
        payload = {
            "first_name": "New Crew",
            "last_name": "New Last Name",
        }
        res = self.client.post(CREW_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Crew.objects.count(), 1)
        crew = Crew.objects.get(id=res.data["id"])
        for key in payload.keys():
            self.assertEqual(getattr(crew, key), payload[key])

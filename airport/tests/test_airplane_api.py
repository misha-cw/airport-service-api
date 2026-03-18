import os
import tempfile

from PIL import Image
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from airport.models import Airplane
from airport.serializers import (
    AirplaneDetailSerializer,
    AirplaneListSerializer,
)
from airport.tests.utils import sample_airplane, sample_airplane_type, sample_flight

AIRPLANE_URL = reverse("airport:airplane-list")


def detail_url(airplane_id):
    return reverse("airport:airplane-detail", args=[airplane_id])


def image_upload_url(airplane_id):
    return reverse("airport:airplane-upload-image", args=[airplane_id])


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
        payload = {
            "name": "New Airplane",
            "rows": 20,
            "seats_in_row": 8,
            "airplane_type": sample_airplane_type().id,
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

    def test_put_airplane_not_allowed(self):
        airplane = sample_airplane()
        payload = {
            "name": "New Airplane",
            "rows": 20,
            "seats_in_row": 8,
            "airplane_type": airplane.airplane_type.id,
        }
        url = detail_url(airplane.id)
        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_airplane_not_allowed(self):
        airplane = sample_airplane()
        res = self.client.delete(detail_url(airplane.id))

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class AirplaneImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            email="admin@test.com", password="adminpassword123", is_staff=True
        )
        self.client.force_authenticate(user=self.user)
        self.airplane = sample_airplane()
        self.flight = sample_flight(airplane=self.airplane)

    def tearDown(self):
        self.airplane.image.delete()

    def test_upload_image_to_airplane(self):
        url = image_upload_url(self.airplane.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")
        self.airplane.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.airplane.image.path))

    def test_upload_image_bad_request(self):
        url = image_upload_url(self.airplane.id)
        res = self.client.post(url, {"image": "not image"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_image_to_airplane_list_should_not_work(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(
                AIRPLANE_URL,
                {
                    "name": "Airbus",
                    "rows": 10,
                    "seats_in_row": 5,
                    "airplane_type": sample_airplane_type().id,
                    "image": ntf,
                },
                format="multipart",
            )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        airplane = Airplane.objects.get(name="Airbus")
        self.assertFalse(airplane.image)

    def test_image_url_is_shown_on_airplane_detail(self):
        url = image_upload_url(self.airplane.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(detail_url(self.airplane.id))

        self.assertIn("image", res.data)

    def test_image_url_is_shown_on_airplane_list(self):
        url = image_upload_url(self.airplane.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")

        res = self.client.get(AIRPLANE_URL)
        self.assertIn("image", res.data[0])

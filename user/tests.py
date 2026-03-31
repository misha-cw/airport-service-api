from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from user.serializers import UserSerializer

CREATE_USER_URL = reverse("user:create")
MANAGE_USER_URL = reverse("user:manage")
USER = get_user_model()


class CreateUserApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_user(self):
        payload = {"email": "user@test.com", "password": "userpassword123"}

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["email"], payload["email"])


class UnauthenticatedManageUserApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(MANAGE_USER_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedManageUserApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = USER.objects.create_user(
            email="user@test.com", password="userpassword123"
        )
        self.client.force_authenticate(user=self.user)

    def test_retrive_user(self):
        res = self.client.get(MANAGE_USER_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        serializer = UserSerializer(self.user)
        self.assertEqual(res.data, serializer.data)

    def test_put_user(self):
        payload = {"email": "user2@test.com", "password": "userpassword1234"}
        res = self.client.put(MANAGE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], payload["email"])

    def test_patch_user(self):
        payload = {
            "email": "user2@test.com",
        }
        res = self.client.patch(MANAGE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], payload["email"])

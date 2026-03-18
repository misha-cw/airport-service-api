from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from airport.models import Route
from airport.serializers import RouteListSerializer, RouteDetailSerializer
from airport.tests.utils import sample_airport, sample_route

ROUTE_URL = reverse("airport:route-list")


def detail_url(route_id):
    return reverse("airport:route-detail", args=[route_id])


class UnauthenticatedRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(ROUTE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@example.com", password="testpassword123"
        )
        self.client.force_authenticate(user=self.user)

    def test_list_routes(self):
        airoport1 = sample_airport(
            name="Airport 1",
        )
        airoport2 = sample_airport(
            name="Airport 2",
        )
        sample_route(source=airoport1, destination=airoport2)
        sample_route(source=airoport2, destination=airoport1)

        res = self.client.get(ROUTE_URL)
        routes = Route.objects.all().order_by("id")
        serializer = RouteListSerializer(routes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_route(self):
        route = sample_route()
        url = detail_url(route.id)
        res = self.client.get(url)

        serializer = RouteDetailSerializer(route)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_route_forbidden(self):
        source = sample_airport(name="Source Airport")
        destination = sample_airport(name="Destination Airport")

        payload = {
            "source": source.id,
            "destination": destination.id,
            "distance": 1500,
        }
        res = self.client.post(ROUTE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_routes_by_source(self):
        source1 = sample_airport(name="Source Airport 1", closest_big_city="City 1")
        source2 = sample_airport(name="Source Airport 2", closest_big_city="City 2")

        route1 = sample_route(source=source1)
        route2 = sample_route(source=source2)

        res = self.client.get(ROUTE_URL, {"source": source1.closest_big_city})

        serializer1 = RouteListSerializer(route1)
        serializer2 = RouteListSerializer(route2)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_filter_routes_by_destination(self):
        destination1 = sample_airport(
            name="Destination Airport 1", closest_big_city="City 1"
        )
        destination2 = sample_airport(
            name="Destination Airport 2", closest_big_city="City 2"
        )

        route1 = sample_route(destination=destination1)
        route2 = sample_route(destination=destination2)

        res = self.client.get(ROUTE_URL, {"destination": destination1.closest_big_city})

        serializer1 = RouteListSerializer(route1)
        serializer2 = RouteListSerializer(route2)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)


class AdminRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = get_user_model().objects.create_superuser(
            email="admin@example.com", password="adminpassword123", is_staff=True
        )
        self.client.force_authenticate(user=self.admin_user)

    def test_create_route(self):
        source = sample_airport(name="Source Airport")
        destination = sample_airport(name="Destination Airport")

        payload = {
            "source": source.id,
            "destination": destination.id,
            "distance": 1500,
        }
        res = self.client.post(ROUTE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Route.objects.count(), 1)
        route = Route.objects.get(id=res.data["id"])
        for key in payload:
            attr = getattr(route, key)
            if hasattr(attr, "id"):
                attr = attr.id

            self.assertEqual(attr, payload[key])

    def test_put_route_not_allowed(self):
        route = sample_route()
        source = sample_airport(name="Source Airport")
        destination = sample_airport(name="Destination Airport")
        payload = {
            "source": source.id,
            "destination": destination.id,
            "distance": 1500,
        }
        url = detail_url(route.id)
        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_route_not_allowed(self):
        route = sample_route()
        res = self.client.delete(detail_url(route.id))

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

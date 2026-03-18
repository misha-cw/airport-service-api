from rest_framework import status
from rest_framework.test import APIClient
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from airport.models import Order, Ticket
from airport.serializers import OrderDetailSerializer, OrderListSerializer
from airport.tests.utils import sample_flight, sample_order, sample_ticket


ORDER_URL = reverse("airport:order-list")


def detail_url(order_id):
    return reverse("airport:order-detail", args=[order_id])


class UnauthenticatedOrderApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(ORDER_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedOrderApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@example.com", password="testpassword123"
        )
        self.client.force_authenticate(user=self.user)

    def test_list_orders(self):
        sample_order(user=self.user)
        sample_order(user=self.user)
        other_user = get_user_model().objects.create_user(
            email="other@test.com", password="otherpassword123"
        )
        sample_order(user=other_user)

        res = self.client.get(ORDER_URL)
        orders = Order.objects.filter(user=self.user)
        serializer = OrderListSerializer(orders, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 2)
        self.assertEqual(res.data["results"], serializer.data)

    def test_list_orders_pagination(self):
        for _ in range(15):
            sample_order(user=self.user)

        res = self.client.get(ORDER_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 15)
        self.assertEqual(len(res.data["results"]), 10)
        self.assertIsNotNone(res.data["next"])
        self.assertIsNone(res.data["previous"])

        res2 = self.client.get(res.data["next"])

        self.assertEqual(len(res2.data["results"]), 5)
        self.assertIsNone(res2.data["next"])
        self.assertIsNotNone(res2.data["previous"])

    def test_retrieve_order(self):
        order = sample_order(user=self.user)
        sample_ticket(order=order)

        res = self.client.get(detail_url(order.id))
        serializer = OrderDetailSerializer(order)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_order(self):
        flight = sample_flight()
        payload = {
            "tickets": [
                {"flight": flight.id, "row": 1, "seat": 1},
                {"flight": flight.id, "row": 1, "seat": 2},
            ]
        }

        res = self.client.post(ORDER_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Ticket.objects.count(), 2)

        order = Order.objects.get(id=res.data["id"])
        tickets = order.tickets.all()

        self.assertEqual(order.user, self.user)

        payload_data = {(t["row"], t["seat"], t["flight"]) for t in payload["tickets"]}
        db_data = {(t.row, t.seat, t.flight.id) for t in tickets}

        self.assertEqual(payload_data, db_data)

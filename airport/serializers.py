from rest_framework import serializers
from django.db import transaction

from airport.models import (
    Airplane,
    AirplaneType,
    Airport,
    Crew,
    Flight,
    Order,
    Route,
    Ticket,
)


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ["id", "name", "closest_big_city"]


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ["id", "source", "destination", "distance"]


class RouteListSerializer(RouteSerializer):
    source = serializers.SlugRelatedField(read_only=True, slug_field="closest_big_city")
    destination = serializers.SlugRelatedField(
        read_only=True, slug_field="closest_big_city"
    )

    class Meta:
        model = Route
        fields = ["id", "source", "destination", "distance"]


class RouteDetailSerializer(RouteSerializer):
    source = AirportSerializer(many=False, read_only=True)
    destination = AirportSerializer(many=False, read_only=True)

    class Meta:
        model = Route
        fields = ["id", "source", "destination", "distance"]


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ["id", "first_name", "last_name"]


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ["id", "name"]


class AirplaneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ["id", "name", "rows", "seats_in_row", "airplane_type"]


class AirplaneListSerializer(AirplaneSerializer):
    airplane_type = serializers.SlugRelatedField(read_only=True, slug_field="name")

    class Meta:
        model = Airplane
        fields = ["id", "name", "total_seats", "airplane_type", "image"]


class AirplaneDetailSerializer(AirplaneSerializer):
    airplane_type = AirplaneTypeSerializer(many=False, read_only=True)

    class Meta:
        model = Airplane
        fields = [
            "id",
            "name",
            "rows",
            "seats_in_row",
            "total_seats",
            "airplane_type",
            "image",
        ]


class AirplaneImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ["id", "image"]


class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = ["id", "route", "airplane", "crew", "departure_time", "arrival_time"]


class FlightListSerializer(FlightSerializer):
    route = serializers.CharField(source="route.route_name", read_only=True)
    airplane = serializers.CharField(source="airplane.name", read_only=True)
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Flight
        fields = [
            "id",
            "route",
            "airplane",
            "departure_time",
            "arrival_time",
            "tickets_available",
        ]


class FlightDetailSerializer(FlightSerializer):
    route = RouteDetailSerializer(many=False, read_only=True)
    airplane = AirplaneListSerializer(many=False, read_only=True)
    crew = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="full_name"
    )


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ["id", "flight", "row", "seat"]


class TicketListSerializer(TicketSerializer):
    flight = FlightListSerializer(many=False, read_only=True)


class TicketSeatsSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = ["row", "seat"]


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = ["id", "tickets", "created_at"]

    def create(self, validated_data):
        with transaction.atomic():
            ticket_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket in ticket_data:
                Ticket.objects.create(order=order, **ticket)
            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)

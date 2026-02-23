from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from airport.models import Airplane, AirplaneType, Airport, Crew, Flight, Order, Route
from airport.serializers import (
    AirplaneDetailSerializer,
    AirplaneImageSerializer,
    AirplaneListSerializer,
    AirplaneSerializer,
    AirplaneTypeSerializer,
    AirportSerializer,
    CrewSerializer,
    FlightDetailSerializer,
    FlightListSerializer,
    FlightSerializer,
    OrderListSerializer,
    OrderSerializer,
    RouteDetailSerializer,
    RouteListSerializer,
    RouteSerializer,
)


class AirportViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer


class RouteViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer

    def get_queryset(self):
        source_closest_sity = self.request.query_params.get("source")
        destination_closest_sity = self.request.query_params.get("destination")

        qs = self.queryset

        if self.action in ["list", "retrieve"]:
            qs = qs.select_related("source", "destination")

        if source_closest_sity:
            qs = qs.filter(source__closest_big_city__icontains=source_closest_sity)

        if destination_closest_sity:
            qs = qs.filter(
                destination__closest_big_city__icontains=destination_closest_sity
            )

        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        if self.action == "retrieve":
            return RouteDetailSerializer

        return RouteSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "source",
                type=OpenApiTypes.STR,
                description="Filter routes by source airport closest big city (case-insensitive, partial match)",
            ),
            OpenApiParameter(
                "destination",
                type=OpenApiTypes.STR,
                description="Filter routes by destination airport closest big city (case-insensitive, partial match)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class CrewViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer


class AirplaneTypeViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer


class AirplaneViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer

    def get_queryset(self):
        qs = self.queryset
        if self.action in ["list", "retrieve"]:
            return qs.select_related("airplane_type")

        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneListSerializer
        if self.action == "retrieve":
            return AirplaneDetailSerializer
        if self.action == "upload_image":
            return AirplaneImageSerializer

        return AirplaneSerializer

    @action(
        detail=True,
        methods=["POST"],
        url_path="upload_image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        airplane = self.get_object()
        serializer = self.get_serializer(airplane, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class FlightViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer

    def get_queryset(self):
        route_id_str = self.request.query_params.get("route")
        departure_time = self.request.query_params.get("departure_time")

        qs = self.queryset

        if self.action in ["list", "retrieve"]:
            qs = qs.select_related(
                "route__source",
                "route__destination",
                "airplane",
            )
        if self.action == "retrieve":
            qs = qs.select_related("airplane__airplane_type").prefetch_related("crew")

        if route_id_str:
            qs = qs.filter(route_id=int(route_id_str))

        if departure_time:
            qs = qs.filter(departure_time__date=departure_time)

        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        if self.action == "retrieve":
            return FlightDetailSerializer

        return FlightSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "route",
                type=OpenApiTypes.INT,
                description="Filter flights by route ID",
            ),
            OpenApiParameter(
                "departure_time",
                type=OpenApiTypes.DATE,
                description="Filter flights by departure date (YYYY-MM-DD)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class OrderPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return OrderListSerializer

        return OrderSerializer

    def get_queryset(self):
        qs = self.queryset.filter(user=self.request.user)
        if self.action in ["list", "retrieve"]:
            return qs.prefetch_related(
                "tickets__flight__route__source",
                "tickets__flight__route__destination",
                "tickets__flight__airplane",
            )
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

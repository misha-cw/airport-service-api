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


def sample_airport(**params) -> Airport:
    defaults = {
        "name": "Sample Airport",
        "closest_big_city": "Sample City",
    }
    defaults.update(params)
    return Airport.objects.create(**defaults)


def sample_route(**params) -> Route:
    source = params.pop("source", sample_airport(name="Source Airport"))
    destination = params.pop("destination", sample_airport(name="Destination Airport"))

    defaults = {
        "source": source,
        "destination": destination,
        "distance": 1000,
    }
    defaults.update(params)
    return Route.objects.create(**defaults)


def sample_airplane_type(**params) -> AirplaneType:
    defaults = {
        "name": "Test Airplane Type",
    }
    defaults.update(params)
    return AirplaneType.objects.create(**defaults)


def sample_airplane(**params) -> Airplane:
    airplane_type = params.pop("airplane_type", sample_airplane_type())

    defaults = {
        "name": "Sample Airplane",
        "rows": 10,
        "seats_in_row": 5,
        "airplane_type": airplane_type,
    }
    defaults.update(params)
    return Airplane.objects.create(**defaults)


def sample_crew(**params) -> Crew:
    defaults = {
        "first_name": "John",
        "last_name": "Doe",
    }
    defaults.update(params)
    return Crew.objects.create(**defaults)


def sample_flight(**params) -> Flight:
    route = params.pop("route", sample_route())
    airplane = params.pop("airplane", sample_airplane())

    defaults = {
        "route": route,
        "airplane": airplane,
        "departure_time": "2024-01-01T10:00:00Z",
        "arrival_time": "2024-01-01T12:00:00Z",
    }
    defaults.update(params)
    return Flight.objects.create(**defaults)


def sample_order(**params) -> Order:
    defaults = {"user": None}
    defaults.update(params)
    return Order.objects.create(**defaults)


def sample_ticket(**params) -> Ticket:
    flight = params.pop("flight", sample_flight())

    defaults = {"row": 1, "seat": 1, "flight": flight, "order": None}
    defaults.update(params)
    return Ticket.objects.create(**defaults)

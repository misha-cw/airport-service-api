from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import UniqueConstraint
from django.core.exceptions import ValidationError


class Airport(models.Model):
    name = models.CharField(max_length=255)
    closest_big_city = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Route(models.Model):
    source = models.ForeignKey(
        Airport, related_name="departing_routes", on_delete=models.CASCADE
    )
    destination = models.ForeignKey(
        Airport, related_name="arriving_routes", on_delete=models.CASCADE
    )
    distance = models.IntegerField()

    class Meta:
        indexes = [
            models.Index(fields=["source", "destination"]),
        ]

    @property
    def route_name(self):
        return f"{self.source} - {self.destination}"

    def __str__(self):
        return f"Route #{self.id}"


class Crew(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name


class AirplaneType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Airplane(models.Model):
    name = models.CharField(max_length=255)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()
    airplane_type = models.ForeignKey(
        AirplaneType, related_name="airplanes", on_delete=models.CASCADE
    )

    @property
    def total_seats(self):
        return self.rows * self.seats_in_row

    def __str__(self):
        return self.name


class Flight(models.Model):
    route = models.ForeignKey(Route, related_name="flights", on_delete=models.CASCADE)
    airplane = models.ForeignKey(
        Airplane, related_name="flights", on_delete=models.CASCADE
    )
    crew = models.ManyToManyField(Crew, related_name="flights")
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["route", "departure_time"]),
        ]
        ordering = ["-departure_time"]

    def __str__(self):
        return f"Flight from {self.route.source} to {self.route.destination} on {self.departure_time}"


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        get_user_model(), related_name="orders", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.created_at} - {self.user.email}"


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    flight = models.ForeignKey(Flight, related_name="tickets", on_delete=models.CASCADE)
    order = models.ForeignKey(Order, related_name="tickets", on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["row", "seat", "flight"], name="unique_seat_per_flight"
            )
        ]

    def __str__(self):
        return f"Ticket for {self.flight} - Row {self.row}, Seat {self.seat}"

    def clean(self):
        if not (1 <= self.row <= self.flight.airplane.rows):
            raise ValidationError(f"Row {self.row} is out of range for this airplane.")
        if not (1 <= self.seat <= self.flight.airplane.seats_in_row):
            raise ValidationError(
                f"Seat {self.seat} is out of range for this airplane."
            )

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.full_clean()
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )

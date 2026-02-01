from django.contrib import admin

from .models import (
    Crew,
    AirplaneType,
    Airplane,
    Airport,
    Route,
    Flight,
    Ticket,
    Order,
)

admin.site.register(Airplane)
admin.site.register(AirplaneType)
admin.site.register(Airport)
admin.site.register(Crew)
admin.site.register(Flight)
admin.site.register(Route)
admin.site.register(Ticket)
admin.site.register(Order)

"""
Guest Controller Interface.
"""

from drivers.mongo.connection import Mongo
from repositories.guest import GuestRepository


class GuestController:
    def _get_repo(self) -> GuestRepository:
        mongo = Mongo()
        return GuestRepository(mongo.get_db())


from interfaces.http.controllers.v1.guest.list import list_active_guests  # noqa
from interfaces.http.controllers.v1.guest.register import register_guest  # noqa
from interfaces.http.controllers.v1.guest.exit import mark_guest_exit  # noqa

GuestController.list_active_guests = list_active_guests
GuestController.register_guest = register_guest
GuestController.mark_guest_exit = mark_guest_exit

controller = GuestController()

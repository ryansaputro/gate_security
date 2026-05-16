"""
Event Controller Interface.
"""

from drivers.mongo.connection import Mongo
from repositories.event import EventRepository


class EventController:
    def _get_repo(self) -> EventRepository:
        mongo = Mongo()
        return EventRepository(mongo.get_db())


from interfaces.http.controllers.v1.event.list import list_events  # noqa
from interfaces.http.controllers.v1.event.create import create_event  # noqa
from interfaces.http.controllers.v1.event.detail import get_event  # noqa
from interfaces.http.controllers.v1.event.delete import delete_event  # noqa

EventController.list_events = list_events
EventController.create_event = create_event
EventController.get_event = get_event
EventController.delete_event = delete_event

controller = EventController()

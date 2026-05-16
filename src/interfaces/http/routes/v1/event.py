"""
Event routes.
"""

from fastapi import APIRouter
from interfaces.http.controllers.v1.event.interface import controller

router = APIRouter(prefix="/events", tags=["Events"])

router.get("")(controller.list_events)
router.get("/{event_id}")(controller.get_event)
router.post("")(controller.create_event)
router.delete("/{event_id}")(controller.delete_event)

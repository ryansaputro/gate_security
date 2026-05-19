"""
Event routes.
"""

from fastapi import APIRouter, Depends
from interfaces.http.controllers.v1.event.interface import controller
from interfaces.http.middlewares.auth import require_auth

router = APIRouter(prefix="/events", tags=["Events"])

_admin_auth = Depends(require_auth(["admin"]))

router.get("", dependencies=[_admin_auth])(controller.list_events)
router.get("/{event_id}", dependencies=[_admin_auth])(controller.get_event)
router.post("", dependencies=[_admin_auth])(controller.create_event)
router.delete("/{event_id}", dependencies=[_admin_auth])(controller.delete_event)

"""
Guest routes.
"""

from fastapi import APIRouter
from interfaces.http.controllers.v1.guest.interface import controller

router = APIRouter(prefix="/guests", tags=["Guests"])

router.get("")(controller.list_active_guests)
router.post("")(controller.register_guest)
router.post("/exit")(controller.mark_guest_exit)

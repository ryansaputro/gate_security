"""
Guest routes.
"""

from fastapi import APIRouter, Depends
from interfaces.http.controllers.v1.guest.interface import controller
from interfaces.http.middlewares.auth import require_auth

router = APIRouter(prefix="/guests", tags=["Guests"])

_admin_auth = Depends(require_auth(["admin"]))

router.get("", dependencies=[_admin_auth])(controller.list_active_guests)
router.post("", dependencies=[_admin_auth])(controller.register_guest)
router.post("/exit", dependencies=[_admin_auth])(controller.mark_guest_exit)

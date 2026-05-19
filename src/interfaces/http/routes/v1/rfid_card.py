"""
RFID Card routes.
"""

from fastapi import APIRouter, Depends
from interfaces.http.controllers.v1.rfid_card.interface import controller
from interfaces.http.middlewares.auth import require_auth

router = APIRouter(prefix="/rfid-cards", tags=["RFID Cards"])

_admin_auth = Depends(require_auth(["admin"]))

router.get("", dependencies=[_admin_auth])(controller.list_cards)
router.get("/{card_id}", dependencies=[_admin_auth])(controller.get_card)
router.post("", dependencies=[_admin_auth])(controller.create_card)
router.post("/block", dependencies=[_admin_auth])(controller.block_card)

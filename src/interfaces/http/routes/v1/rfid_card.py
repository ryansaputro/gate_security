"""
RFID Card routes.
"""

from fastapi import APIRouter
from interfaces.http.controllers.v1.rfid_card.interface import controller

router = APIRouter(prefix="/rfid-cards", tags=["RFID Cards"])

router.get("")(controller.list_cards)
router.get("/{card_id}")(controller.get_card)
router.post("")(controller.create_card)
router.post("/block")(controller.block_card)

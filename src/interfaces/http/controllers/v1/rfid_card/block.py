"""
RFID Card Controller - Block card.
"""

from fastapi import HTTPException
from helpers.serializers.rfid_card import RfidCardBlock
from definitions.applications.response import SuccessResponse


def block_card(self, body: RfidCardBlock) -> SuccessResponse:
    """Block/deactivate an RFID card."""
    repo = self._get_repo()
    card = repo.find_by_id(body.card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    repo.block_card(body.card_id, body.reason)
    card = repo.find_by_id(body.card_id)
    return SuccessResponse(data={
        "id": card.id,
        "card_uid": card.card_uid,
        "is_active": card.is_active,
        "blocked_reason": card.blocked_reason,
    })

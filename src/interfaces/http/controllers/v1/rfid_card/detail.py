"""
RFID Card Controller - Get card detail.
"""

from fastapi import HTTPException
from definitions.applications.response import SuccessResponse


def get_card(self, card_id: str) -> SuccessResponse:
    """Get RFID card by ID."""
    repo = self._get_repo()
    c = repo.find_by_id(card_id)
    if not c:
        raise HTTPException(status_code=404, detail="Card not found")
    return SuccessResponse(data={
        "id": c.id,
        "card_uid": c.card_uid,
        "family_id": c.family_id,
        "holder_name": c.holder_name,
        "vehicle_ids": c.vehicle_ids,
        "card_type": c.card_type,
        "is_active": c.is_active,
        "blocked_reason": c.blocked_reason,
    })

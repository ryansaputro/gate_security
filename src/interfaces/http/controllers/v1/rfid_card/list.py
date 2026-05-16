"""
RFID Card Controller - List cards.
"""

from typing import Optional
from definitions.applications.response import SuccessResponse


def list_cards(self, family_id: Optional[str] = None, skip: int = 0, limit: int = 50) -> SuccessResponse:
    """List RFID cards, optionally filter by family_id."""
    repo = self._get_repo()
    if family_id:
        cards = repo.find_by_family_id(family_id)
    else:
        cards = repo.find_many(skip=skip, limit=limit)
    return SuccessResponse(data=[{
        "id": c.id,
        "card_uid": c.card_uid,
        "family_id": c.family_id,
        "holder_name": c.holder_name,
        "card_type": c.card_type,
        "is_active": c.is_active,
    } for c in cards])

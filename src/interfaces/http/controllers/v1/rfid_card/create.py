"""
RFID Card Controller - Create card.
"""

from datetime import datetime
from helpers.serializers.rfid_card import RfidCardCreate
from definitions.applications.response import SuccessResponse
from entities.rfid_card import RfidCard


def create_card(self, body: RfidCardCreate) -> SuccessResponse:
    """Register a new RFID card."""
    repo = self._get_repo()
    entity = RfidCard(
        card_uid=body.card_uid,
        family_id=body.family_id,
        holder_name=body.holder_name,
        vehicle_ids=body.vehicle_ids,
        card_type=body.card_type,
        is_active=True,
        issued_at=datetime.now(),
    )
    cid = repo.create(entity)
    card = repo.find_by_id(cid)
    return SuccessResponse(data={
        "id": card.id,
        "card_uid": card.card_uid,
        "holder_name": card.holder_name,
        "card_type": card.card_type,
        "is_active": card.is_active,
    })

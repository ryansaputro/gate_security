"""
Guest Controller - Register guest entry.
"""

from datetime import datetime
from helpers.serializers.guest import GuestCreate
from definitions.applications.response import SuccessResponse
from entities.guest import Guest


def register_guest(self, body: GuestCreate) -> SuccessResponse:
    """Register a new guest entry."""
    repo = self._get_repo()
    entity = Guest(
        visiting_house_id=body.visiting_house_id,
        guest_name=body.guest_name,
        guest_phone=body.guest_phone,
        purpose=body.purpose,
        vehicle_plate=body.vehicle_plate,
        vehicle_type=body.vehicle_type,
        entry_time=datetime.now(),
        status="inside",
    )
    gid = repo.create(entity)
    guest = repo.find_by_id(gid)
    return SuccessResponse(data={
        "id": guest.id,
        "guest_name": guest.guest_name,
        "status": guest.status,
        "entry_time": guest.entry_time.isoformat() if guest.entry_time else None,
    })

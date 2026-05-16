"""
Guest Controller - List active guests.
"""

from definitions.applications.response import SuccessResponse


def list_active_guests(self) -> SuccessResponse:
    """List all guests currently inside the complex."""
    repo = self._get_repo()
    guests = repo.find_active_guests()
    return SuccessResponse(data=[_serialize(g) for g in guests])


def _serialize(g) -> dict:
    return {
        "id": g.id,
        "visiting_house_id": g.visiting_house_id,
        "guest_name": g.guest_name,
        "guest_phone": g.guest_phone,
        "purpose": g.purpose,
        "vehicle_plate": g.vehicle_plate,
        "vehicle_type": g.vehicle_type,
        "entry_time": g.entry_time.isoformat() if g.entry_time else None,
        "status": g.status,
    }

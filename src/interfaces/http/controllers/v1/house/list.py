"""
House Controller - List houses.
"""

from typing import Optional
from definitions.applications.response import SuccessResponse


def list_houses(self, block: Optional[str] = None, skip: int = 0, limit: int = 50) -> SuccessResponse:
    """List all houses, optionally filter by block."""
    repo = self._get_repo()
    if block:
        houses = repo.find_by_block(block)
    else:
        houses = repo.find_many(skip=skip, limit=limit)
    return SuccessResponse(data=[_serialize(h) for h in houses])


def _serialize(h) -> dict:
    return {
        "id": h.id,
        "block": h.block,
        "street": h.street,
        "house_number": h.house_number,
        "status": h.status,
        "latitude": h.latitude,
        "longitude": h.longitude,
        "address_note": h.address_note,
    }

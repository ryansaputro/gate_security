"""
Vehicle Controller - List vehicles.
"""

from typing import Optional
from definitions.applications.response import SuccessResponse


def list_vehicles(self, family_id: Optional[str] = None, skip: int = 0, limit: int = 50) -> SuccessResponse:
    """List vehicles, optionally filter by family_id."""
    repo = self._get_repo()
    if family_id:
        vehicles = repo.find_by_family_id(family_id)
    else:
        vehicles = repo.find_many(skip=skip, limit=limit)
    return SuccessResponse(data=[_serialize(v) for v in vehicles])


def _serialize(v) -> dict:
    return {
        "id": v.id,
        "family_id": v.family_id,
        "plate_number": v.plate_number,
        "plate_number_normalized": v.plate_number_normalized,
        "type": v.type,
        "brand": v.brand,
        "model": v.model,
        "color": v.color,
        "year": v.year,
        "is_active": v.is_active,
    }

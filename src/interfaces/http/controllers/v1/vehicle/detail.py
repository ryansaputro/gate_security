"""
Vehicle Controller - Get vehicle detail.
"""

from fastapi import HTTPException
from definitions.applications.response import SuccessResponse


def get_vehicle(self, vehicle_id: str) -> SuccessResponse:
    """Get vehicle by ID."""
    repo = self._get_repo()
    vehicle = repo.find_by_id(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return SuccessResponse(data={
        "id": vehicle.id,
        "family_id": vehicle.family_id,
        "plate_number": vehicle.plate_number,
        "plate_number_normalized": vehicle.plate_number_normalized,
        "type": vehicle.type,
        "brand": vehicle.brand,
        "model": vehicle.model,
        "color": vehicle.color,
        "year": vehicle.year,
        "is_active": vehicle.is_active,
    })

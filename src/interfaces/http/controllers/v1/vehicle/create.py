"""
Vehicle Controller - Create vehicle.
"""

from helpers.serializers.vehicle import VehicleCreate
from definitions.applications.response import SuccessResponse
from entities.vehicle import Vehicle


def create_vehicle(self, body: VehicleCreate) -> SuccessResponse:
    """Register a new vehicle."""
    repo = self._get_repo()
    normalized = body.plate_number.replace(" ", "").upper()
    entity = Vehicle(
        family_id=body.family_id,
        plate_number=body.plate_number,
        plate_number_normalized=normalized,
        type=body.type,
        brand=body.brand,
        model=body.model,
        color=body.color,
        year=body.year,
    )
    vid = repo.create(entity)
    vehicle = repo.find_by_id(vid)
    return SuccessResponse(data={
        "id": vehicle.id,
        "family_id": vehicle.family_id,
        "plate_number": vehicle.plate_number,
        "plate_number_normalized": vehicle.plate_number_normalized,
        "type": vehicle.type,
    })

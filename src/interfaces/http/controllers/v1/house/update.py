"""
House Controller - Update house.
"""

from fastapi import HTTPException
from helpers.serializers.house import HouseCreate
from definitions.applications.response import SuccessResponse


def update_house(self, house_id: str, body: HouseCreate) -> SuccessResponse:
    """Update house data."""
    repo = self._get_repo()
    existing = repo.find_by_id(house_id)
    if not existing:
        raise HTTPException(status_code=404, detail="House not found")
    repo.update_by_id(house_id, {
        "block": body.block,
        "street": body.street,
        "houseNumber": body.house_number,
        "status": body.status,
        "latitude": body.latitude,
        "longitude": body.longitude,
        "addressNote": body.address_note,
    })
    house = repo.find_by_id(house_id)
    return SuccessResponse(data={
        "id": house.id,
        "block": house.block,
        "street": house.street,
        "house_number": house.house_number,
        "status": house.status,
    })

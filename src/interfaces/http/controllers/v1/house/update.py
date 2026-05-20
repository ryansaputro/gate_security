"""
House Controller - Update house.
"""

from fastapi import HTTPException
from helpers.serializers.house import HouseCreate
from definitions.applications.response import SuccessResponse


def update_house(self, house_id: str, body: HouseCreate) -> SuccessResponse:
    """Update house data."""
    house = self.uc.update(
        house_id=house_id,
        block=body.block,
        house_number=body.house_number,
        street=body.street,
        status=body.status,
        address_note=body.address_note,
        latitude=body.latitude,
        longitude=body.longitude,
    )
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    return SuccessResponse(data=self.uc.serialize(house))

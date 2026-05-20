"""
House Controller - Create house.
"""

from helpers.serializers.house import HouseCreate
from definitions.applications.response import SuccessResponse


def create_house(self, body: HouseCreate) -> SuccessResponse:
    """Create a new house."""
    house = self.uc.create(
        block=body.block,
        house_number=body.house_number,
        street=body.street,
        status=body.status,
        address_note=body.address_note,
        latitude=body.latitude,
        longitude=body.longitude,
    )
    return SuccessResponse(data=self.uc.serialize(house))

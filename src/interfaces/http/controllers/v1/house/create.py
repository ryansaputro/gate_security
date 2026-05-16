"""
House Controller - Create house.
"""

from helpers.serializers.house import HouseCreate
from definitions.applications.response import SuccessResponse
from entities.house import House


def create_house(self, body: HouseCreate) -> SuccessResponse:
    """Create a new house."""
    repo = self._get_repo()
    entity = House(
        block=body.block,
        street=body.street,
        house_number=body.house_number,
        status=body.status,
        latitude=body.latitude,
        longitude=body.longitude,
        address_note=body.address_note,
    )
    house_id = repo.create(entity)
    house = repo.find_by_id(house_id)
    return SuccessResponse(data={
        "id": house.id,
        "block": house.block,
        "street": house.street,
        "house_number": house.house_number,
        "status": house.status,
    })

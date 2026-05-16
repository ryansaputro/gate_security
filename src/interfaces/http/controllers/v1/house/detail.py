"""
House Controller - Get house detail.
"""

from fastapi import HTTPException
from definitions.applications.response import SuccessResponse


def get_house(self, house_id: str) -> SuccessResponse:
    """Get house by ID."""
    repo = self._get_repo()
    house = repo.find_by_id(house_id)
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    return SuccessResponse(data={
        "id": house.id,
        "block": house.block,
        "street": house.street,
        "house_number": house.house_number,
        "status": house.status,
        "latitude": house.latitude,
        "longitude": house.longitude,
        "address_note": house.address_note,
    })

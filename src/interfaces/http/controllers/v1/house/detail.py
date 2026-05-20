"""
House Controller - Get house detail.
"""

from fastapi import HTTPException
from definitions.applications.response import SuccessResponse


def get_house(self, house_id: str) -> SuccessResponse:
    """Get house by ID."""
    house = self.uc.find_by_id(house_id)
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    return SuccessResponse(data=self.uc.serialize(house))

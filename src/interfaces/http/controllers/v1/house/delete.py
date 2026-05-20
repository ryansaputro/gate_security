"""
House Controller - Delete house.
"""

from fastapi import HTTPException
from definitions.applications.response import SuccessResponse


def delete_house(self, house_id: str) -> SuccessResponse:
    """Delete a house."""
    deleted = self.uc.delete(house_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="House not found")
    return SuccessResponse(message="deleted")

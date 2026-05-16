"""
House Controller - Delete house.
"""

from fastapi import HTTPException
from definitions.applications.response import SuccessResponse


def delete_house(self, house_id: str) -> SuccessResponse:
    """Delete a house."""
    repo = self._get_repo()
    existing = repo.find_by_id(house_id)
    if not existing:
        raise HTTPException(status_code=404, detail="House not found")
    repo.delete_by_id(house_id)
    return SuccessResponse(message="deleted")

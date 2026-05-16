"""
Family Controller - Delete family.
"""

from fastapi import HTTPException
from definitions.applications.response import SuccessResponse


def delete_family(self, family_id: str) -> SuccessResponse:
    """Delete a family record."""
    repo = self._get_repo()
    if not repo.find_by_id(family_id):
        raise HTTPException(status_code=404, detail="Family not found")
    repo.delete_by_id(family_id)
    return SuccessResponse(message="deleted")

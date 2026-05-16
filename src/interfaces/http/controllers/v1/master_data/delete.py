"""
Master Data Controller - Delete master data.
"""

from fastapi import HTTPException
from definitions.applications.response import SuccessResponse


def delete_master_data(self, master_id: str) -> SuccessResponse:
    """Delete a master data entry."""
    repo = self._get_repo()
    if not repo.find_by_id(master_id):
        raise HTTPException(status_code=404, detail="Master data not found")
    repo.delete_by_id(master_id)
    return SuccessResponse(message="deleted")

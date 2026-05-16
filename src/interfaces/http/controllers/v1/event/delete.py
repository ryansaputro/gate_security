"""
Event Controller - Delete event.
"""

from fastapi import HTTPException
from definitions.applications.response import SuccessResponse


def delete_event(self, event_id: str) -> SuccessResponse:
    """Delete an event."""
    repo = self._get_repo()
    if not repo.find_by_id(event_id):
        raise HTTPException(status_code=404, detail="Event not found")
    repo.delete_by_id(event_id)
    return SuccessResponse(message="deleted")

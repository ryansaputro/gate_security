"""
Event Controller - List events.
"""

from typing import Optional
from definitions.applications.response import SuccessResponse


def list_events(self, status: Optional[str] = None) -> SuccessResponse:
    """List events, optionally filter by status."""
    repo = self._get_repo()
    if status:
        events = repo.find_by_status(status)
    else:
        events = repo.find_upcoming()
    return SuccessResponse(data=[{
        "id": e.id,
        "title": e.title,
        "type": e.type,
        "location": e.location,
        "start_date": e.start_date.isoformat() if e.start_date else None,
        "status": e.status,
    } for e in events])

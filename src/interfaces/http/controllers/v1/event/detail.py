"""
Event Controller - Get event detail.
"""

from fastapi import HTTPException
from definitions.applications.response import SuccessResponse


def get_event(self, event_id: str) -> SuccessResponse:
    """Get event by ID."""
    repo = self._get_repo()
    e = repo.find_by_id(event_id)
    if not e:
        raise HTTPException(status_code=404, detail="Event not found")
    return SuccessResponse(data={
        "id": e.id,
        "title": e.title,
        "description": e.description,
        "type": e.type,
        "location": e.location,
        "start_date": e.start_date.isoformat() if e.start_date else None,
        "end_date": e.end_date.isoformat() if e.end_date else None,
        "organizer": e.organizer,
        "target_audience": e.target_audience,
        "is_mandatory": e.is_mandatory,
        "status": e.status,
    })

"""
Event Controller - Create event.
"""

from datetime import datetime
from helpers.serializers.event import EventCreate
from definitions.applications.response import SuccessResponse
from entities.event import Event


def create_event(self, body: EventCreate) -> SuccessResponse:
    """Create a new community event."""
    repo = self._get_repo()
    entity = Event(
        title=body.title,
        description=body.description,
        type=body.type,
        location=body.location,
        start_date=datetime.fromisoformat(body.start_date) if body.start_date else None,
        end_date=datetime.fromisoformat(body.end_date) if body.end_date else None,
        organizer=body.organizer,
        target_audience=body.target_audience,
        is_mandatory=body.is_mandatory,
        status="upcoming",
    )
    eid = repo.create(entity)
    e = repo.find_by_id(eid)
    return SuccessResponse(data={"id": e.id, "title": e.title, "status": e.status})

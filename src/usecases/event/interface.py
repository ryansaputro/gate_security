"""
Event Usecase - shared business logic for community events.
"""

from datetime import datetime
from typing import List, Optional, Tuple

from entities.event import Event


class EventUsecase:
    def __init__(self):
        self._repo = None

    @property
    def repo(self):
        if self._repo is None:
            from drivers.mongo.connection import Mongo
            from repositories.event import EventRepository
            mongo = Mongo()
            self._repo = EventRepository(mongo.get_db())
        return self._repo

    def list(self, search: Optional[str] = None, page: int = 1, per_page: int = 20) -> Tuple[List[Event], int, int, int]:
        """List events with pagination and search."""
        query = {}
        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"location": {"$regex": search, "$options": "i"}},
            ]
        total = self.repo.count(query)
        total_pages = max(1, (total + per_page - 1) // per_page)
        if page < 1:
            page = 1
        items = self.repo.find_many(
            filter=query,
            sort=[("startDate", -1)],
            skip=(page - 1) * per_page,
            limit=per_page,
        )
        return items, page, total_pages, total

    def find_by_id(self, event_id: str) -> Optional[Event]:
        """Get a single event by ID."""
        return self.repo.find_by_id(event_id)

    def create(self, title: str, description: str = "", type: str = "announcement",
               location: str = "", start_date: str = "", end_date: str = "",
               organizer: str = "", target_audience: str = "all",
               is_mandatory: bool = False, status: str = "upcoming") -> Event:
        """Create a new event."""
        entity = Event(
            title=title,
            description=description,
            type=type,
            location=location,
            start_date=_parse_datetime(start_date),
            end_date=_parse_datetime(end_date),
            organizer=organizer,
            target_audience=target_audience,
            is_mandatory=is_mandatory,
            status=status,
        )
        event_id = self.repo.create(entity)
        return self.repo.find_by_id(event_id)

    def update(self, event_id: str, title: str = "", description: str = "",
               type: str = "announcement", location: str = "",
               start_date: str = "", end_date: str = "",
               organizer: str = "", target_audience: str = "all",
               is_mandatory: bool = False, status: str = "upcoming") -> Optional[Event]:
        """Update an event."""
        existing = self.repo.find_by_id(event_id)
        if not existing:
            return None
        update_fields = {
            "title": title,
            "description": description,
            "type": type,
            "location": location,
            "startDate": _parse_datetime(start_date),
            "endDate": _parse_datetime(end_date),
            "organizer": organizer,
            "targetAudience": target_audience,
            "isMandatory": is_mandatory,
            "status": status,
            "updatedAt": datetime.now(),
        }
        self.repo.update_by_id(event_id, update_fields)
        return self.repo.find_by_id(event_id)

    def delete(self, event_id: str) -> bool:
        """Delete an event."""
        existing = self.repo.find_by_id(event_id)
        if not existing:
            return False
        return self.repo.delete_by_id(event_id)

    def serialize(self, event: Event) -> dict:
        """Serialize event entity to dict."""
        return {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "type": event.type,
            "location": event.location,
            "start_date": event.start_date,
            "end_date": event.end_date,
            "organizer": event.organizer,
            "target_audience": event.target_audience,
            "is_mandatory": event.is_mandatory,
            "status": event.status,
        }


def _parse_datetime(value: str) -> Optional[datetime]:
    """Parse datetime string from HTML input (YYYY-MM-DDTHH:MM or YYYY-MM-DD)."""
    if not value:
        return None
    try:
        if "T" in value:
            return datetime.fromisoformat(value)
        return datetime.strptime(value, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


# Singleton instance
event_usecase = EventUsecase()

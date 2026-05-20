"""
Event Usecase - shared business logic for community events.
List + find_by_id only.
"""

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
        """List events with pagination and search. Returns (items, page, total_pages, total)."""
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
            "status": event.status,
        }


# Singleton instance
event_usecase = EventUsecase()

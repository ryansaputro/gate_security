from typing import List
from repositories.base import BaseRepository
from models import event as event_model


class EventRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, event_model.COLLECTION_NAME, event_model)

    def find_upcoming(self) -> List:
        return self.find_many({"status": "upcoming"}, sort=[("startDate", 1)])

    def find_by_status(self, status: str) -> List:
        return self.find_many({"status": status}, sort=[("startDate", -1)])

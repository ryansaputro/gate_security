from typing import List
from repositories.base import BaseRepository
from models import access_log as log_model


class AccessLogRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, log_model.COLLECTION_NAME, log_model)

    def find_recent(self, limit: int = 50) -> List:
        return self.find_many({}, sort=[("timestamp", -1)], limit=limit)

    def find_by_plate(self, plate: str, limit: int = 10) -> List:
        return self.find_many(
            {"plateDetected": plate},
            sort=[("timestamp", -1)],
            limit=limit
        )

    def find_by_rfid(self, card_id: str, limit: int = 10) -> List:
        return self.find_many(
            {"rfidCardId": card_id},
            sort=[("timestamp", -1)],
            limit=limit
        )

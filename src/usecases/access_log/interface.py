"""
Access Log Usecase - shared business logic for access logs.
List only (read-only, no CRUD).
"""

from typing import List, Optional, Tuple

from entities.access_log import AccessLog


class AccessLogUsecase:
    def __init__(self):
        self._repo = None

    @property
    def repo(self):
        if self._repo is None:
            from drivers.mongo.connection import Mongo
            from repositories.access_log import AccessLogRepository
            mongo = Mongo()
            self._repo = AccessLogRepository(mongo.get_db())
        return self._repo

    def list(self, search: Optional[str] = None, page: int = 1, per_page: int = 20) -> Tuple[List[AccessLog], int, int, int]:
        """List access logs with pagination and search. Returns (items, page, total_pages, total)."""
        query = {}
        if search:
            query["$or"] = [
                {"plateDetected": {"$regex": search, "$options": "i"}},
                {"gateId": {"$regex": search, "$options": "i"}},
            ]
        total = self.repo.count(query)
        total_pages = max(1, (total + per_page - 1) // per_page)
        if page < 1:
            page = 1
        items = self.repo.find_many(
            filter=query,
            sort=[("timestamp", -1)],
            skip=(page - 1) * per_page,
            limit=per_page,
        )
        return items, page, total_pages, total

    def find_by_id(self, log_id: str) -> Optional[AccessLog]:
        """Get a single access log by ID."""
        return self.repo.find_by_id(log_id)

    def serialize(self, log: AccessLog) -> dict:
        """Serialize access log entity to dict."""
        return {
            "id": log.id,
            "gate_id": log.gate_id,
            "direction": log.direction,
            "method": log.method,
            "plate_detected": log.plate_detected,
            "plate_confidence": log.plate_confidence,
            "validation_result": log.validation_result,
            "denied_reason": log.denied_reason,
            "timestamp": log.timestamp,
        }


# Singleton instance
access_log_usecase = AccessLogUsecase()

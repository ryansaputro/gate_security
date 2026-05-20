"""
Guest Usecase - shared business logic for guests.
List only (no create/update from admin, guests come from gate).
"""

from typing import List, Optional, Tuple

from entities.guest import Guest


class GuestUsecase:
    def __init__(self):
        self._repo = None

    @property
    def repo(self):
        if self._repo is None:
            from drivers.mongo.connection import Mongo
            from repositories.guest import GuestRepository
            mongo = Mongo()
            self._repo = GuestRepository(mongo.get_db())
        return self._repo

    def list(self, search: Optional[str] = None, page: int = 1, per_page: int = 20) -> Tuple[List[Guest], int, int, int]:
        """List guests with pagination and search. Returns (items, page, total_pages, total)."""
        query = {}
        if search:
            query["$or"] = [
                {"guestName": {"$regex": search, "$options": "i"}},
                {"guestPhone": {"$regex": search, "$options": "i"}},
                {"vehiclePlate": {"$regex": search, "$options": "i"}},
            ]
        total = self.repo.count(query)
        total_pages = max(1, (total + per_page - 1) // per_page)
        if page < 1:
            page = 1
        items = self.repo.find_many(
            filter=query,
            sort=[("entryTime", -1)],
            skip=(page - 1) * per_page,
            limit=per_page,
        )
        return items, page, total_pages, total

    def find_by_id(self, guest_id: str) -> Optional[Guest]:
        """Get a single guest by ID."""
        return self.repo.find_by_id(guest_id)

    def serialize(self, guest: Guest) -> dict:
        """Serialize guest entity to dict."""
        return {
            "id": guest.id,
            "guest_name": guest.guest_name,
            "guest_phone": guest.guest_phone,
            "purpose": guest.purpose,
            "vehicle_plate": guest.vehicle_plate,
            "vehicle_type": guest.vehicle_type,
            "entry_time": guest.entry_time,
            "exit_time": guest.exit_time,
            "status": guest.status,
        }


# Singleton instance
guest_usecase = GuestUsecase()

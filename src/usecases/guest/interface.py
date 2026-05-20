"""
Guest Usecase - shared business logic for guests.
"""

from datetime import datetime
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

    def create(self, guest_name: str, guest_phone: str = "", guest_id_number: str = "",
               purpose: str = "visit", vehicle_plate: str = "", vehicle_type: str = "none",
               visiting_house_id: str = "", visiting_family_id: str = "",
               entry_gate: str = "gate_1", approved_by: str = "security",
               notes: str = "", status: str = "inside",
               max_duration_hours: int = 0) -> Guest:
        """Register a new guest."""
        entity = Guest(
            guest_name=guest_name,
            guest_phone=guest_phone,
            guest_id_number=guest_id_number,
            purpose=purpose,
            vehicle_plate=vehicle_plate.upper().replace(" ", "") if vehicle_plate else "",
            vehicle_type=vehicle_type,
            visiting_house_id=visiting_house_id,
            visiting_family_id=visiting_family_id,
            entry_gate=entry_gate,
            approved_by=approved_by,
            notes=notes,
            status=status,
            max_duration_hours=max_duration_hours,
            entry_time=datetime.now(),
        )
        guest_id = self.repo.create(entity)
        return self.repo.find_by_id(guest_id)

    def update(self, guest_id: str, guest_name: str = "", guest_phone: str = "",
               guest_id_number: str = "", purpose: str = "visit",
               vehicle_plate: str = "", vehicle_type: str = "none",
               visiting_house_id: str = "", visiting_family_id: str = "",
               approved_by: str = "", notes: str = "", status: str = "inside",
               max_duration_hours: int = 0) -> Optional[Guest]:
        """Update a guest record."""
        existing = self.repo.find_by_id(guest_id)
        if not existing:
            return None
        update_fields = {
            "guestName": guest_name,
            "guestPhone": guest_phone,
            "guestIdNumber": guest_id_number,
            "purpose": purpose,
            "vehiclePlate": vehicle_plate.upper().replace(" ", "") if vehicle_plate else "",
            "vehicleType": vehicle_type,
            "visitingHouseId": visiting_house_id,
            "visitingFamilyId": visiting_family_id,
            "approvedBy": approved_by,
            "notes": notes,
            "status": status,
            "maxDurationHours": max_duration_hours,
        }
        # Set exit time if status changed to exited
        if status == "exited" and existing.status != "exited":
            update_fields["exitTime"] = datetime.now()
        self.repo.update_by_id(guest_id, update_fields)
        return self.repo.find_by_id(guest_id)

    def delete(self, guest_id: str) -> bool:
        """Delete a guest record."""
        existing = self.repo.find_by_id(guest_id)
        if not existing:
            return False
        return self.repo.delete_by_id(guest_id)

    def checkout(self, guest_id: str, exit_gate: str = "gate_1") -> Optional[Guest]:
        """Mark guest as exited."""
        self.repo.mark_exited(guest_id, exit_gate)
        return self.repo.find_by_id(guest_id)

    def serialize(self, guest: Guest) -> dict:
        """Serialize guest entity to dict."""
        return {
            "id": guest.id,
            "guest_name": guest.guest_name,
            "guest_phone": guest.guest_phone,
            "guest_id_number": guest.guest_id_number,
            "purpose": guest.purpose,
            "vehicle_plate": guest.vehicle_plate,
            "vehicle_type": guest.vehicle_type,
            "visiting_house_id": guest.visiting_house_id,
            "visiting_family_id": guest.visiting_family_id,
            "entry_time": guest.entry_time,
            "exit_time": guest.exit_time,
            "entry_gate": guest.entry_gate,
            "approved_by": guest.approved_by,
            "status": guest.status,
            "notes": guest.notes,
            "max_duration_hours": guest.max_duration_hours if hasattr(guest, 'max_duration_hours') else 0,
        }


# Singleton instance
guest_usecase = GuestUsecase()

from datetime import datetime
from typing import List
from repositories.base import BaseRepository
from models import guest as guest_model


class GuestRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, guest_model.COLLECTION_NAME, guest_model)

    def find_active_guests(self) -> List:
        return self.find_many({"status": "inside"}, sort=[("entryTime", -1)])

    def find_by_plate(self, plate: str):
        return self.find_one({"vehiclePlate": plate, "status": "inside"})

    def mark_exited(self, id: str, exit_gate: str) -> bool:
        return self.update_by_id(id, {
            "status": "exited",
            "exitTime": datetime.now(),
            "exitGate": exit_gate,
        })

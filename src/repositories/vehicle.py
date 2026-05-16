from typing import List, Optional
from repositories.base import BaseRepository
from models import vehicle as vehicle_model


class VehicleRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, vehicle_model.COLLECTION_NAME, vehicle_model)

    def find_by_plate(self, plate_normalized: str):
        return self.find_one({"plateNumberNormalized": plate_normalized})

    def find_by_family_id(self, family_id: str) -> List:
        return self.find_many({"familyId": family_id, "isActive": True})

    def find_by_plate_contains(self, partial_plate: str) -> List:
        """Fuzzy search: find plates containing partial string."""
        import re
        pattern = re.compile(re.escape(partial_plate), re.IGNORECASE)
        return self.find_many({"plateNumberNormalized": {"$regex": pattern}})

    def find_all_active_plates(self) -> List[str]:
        """Get all active plate numbers for fuzzy matching."""
        docs = self.collection.find(
            {"isActive": True},
            {"plateNumberNormalized": 1}
        )
        return [doc["plateNumberNormalized"] for doc in docs]

"""
Vehicle Usecase - shared business logic for vehicles.
Used by both API controller and Web admin panel.
"""

import re
from typing import List, Optional, Tuple

from entities.vehicle import Vehicle


class VehicleUsecase:
    def __init__(self):
        self._repo = None

    @property
    def repo(self):
        if self._repo is None:
            from drivers.mongo.connection import Mongo
            from repositories.vehicle import VehicleRepository
            mongo = Mongo()
            self._repo = VehicleRepository(mongo.get_db())
        return self._repo

    def list(self, search: Optional[str] = None, page: int = 1, per_page: int = 20) -> Tuple[List[Vehicle], int, int, int]:
        """List vehicles with pagination and search. Returns (items, page, total_pages, total)."""
        query = {}
        if search:
            query["$or"] = [
                {"plateNumber": {"$regex": search, "$options": "i"}},
                {"brand": {"$regex": search, "$options": "i"}},
                {"model": {"$regex": search, "$options": "i"}},
                {"color": {"$regex": search, "$options": "i"}},
            ]
        total = self.repo.count(query)
        total_pages = max(1, (total + per_page - 1) // per_page)
        if page < 1:
            page = 1
        items = self.repo.find_many(
            filter=query,
            sort=[("plateNumber", 1)],
            skip=(page - 1) * per_page,
            limit=per_page,
        )
        return items, page, total_pages, total

    def find_by_id(self, vehicle_id: str) -> Optional[Vehicle]:
        """Get a single vehicle by ID."""
        return self.repo.find_by_id(vehicle_id)

    def create(self, plate_number: str, type: str = "car", brand: str = "",
               model: str = "", color: str = "", year: int = 0,
               is_active: bool = True, family_id: str = "") -> Vehicle:
        """Create a new vehicle and return it."""
        plate_number_normalized = re.sub(r"[^A-Z0-9]", "", plate_number.upper())
        entity = Vehicle(
            plate_number=plate_number,
            plate_number_normalized=plate_number_normalized,
            type=type,
            brand=brand,
            model=model,
            color=color,
            year=year,
            is_active=is_active,
            family_id=family_id,
        )
        vehicle_id = self.repo.create(entity)
        return self.repo.find_by_id(vehicle_id)

    def update(self, vehicle_id: str, plate_number: str = "", type: str = "car",
               brand: str = "", model: str = "", color: str = "",
               year: int = 0, is_active: bool = True, family_id: str = "") -> Optional[Vehicle]:
        """Update a vehicle. Returns updated vehicle or None if not found."""
        existing = self.repo.find_by_id(vehicle_id)
        if not existing:
            return None
        plate_number_normalized = re.sub(r"[^A-Z0-9]", "", plate_number.upper())
        update_fields = {
            "plateNumber": plate_number,
            "plateNumberNormalized": plate_number_normalized,
            "type": type,
            "brand": brand,
            "model": model,
            "color": color,
            "year": year,
            "isActive": is_active,
            "familyId": family_id,
        }
        self.repo.update_by_id(vehicle_id, update_fields)
        return self.repo.find_by_id(vehicle_id)

    def delete(self, vehicle_id: str) -> bool:
        """Delete a vehicle. Returns True if deleted, False if not found."""
        existing = self.repo.find_by_id(vehicle_id)
        if not existing:
            return False
        return self.repo.delete_by_id(vehicle_id)

    def serialize(self, vehicle: Vehicle) -> dict:
        """Serialize vehicle entity to dict."""
        return {
            "id": vehicle.id,
            "plate_number": vehicle.plate_number,
            "type": vehicle.type,
            "brand": vehicle.brand,
            "model": vehicle.model,
            "color": vehicle.color,
            "year": vehicle.year,
            "is_active": vehicle.is_active,
            "family_id": vehicle.family_id if hasattr(vehicle, 'family_id') else "",
        }


# Singleton instance
vehicle_usecase = VehicleUsecase()

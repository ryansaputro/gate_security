"""
House Usecase - shared business logic for houses.
Used by both API controller and Web admin panel.
"""

from typing import List, Optional, Tuple
from dataclasses import asdict

from drivers.mongo.connection import Mongo
from repositories.house import HouseRepository
from entities.house import House


class HouseUsecase:
    def __init__(self):
        self._repo = None

    @property
    def repo(self) -> HouseRepository:
        if self._repo is None:
            mongo = Mongo()
            self._repo = HouseRepository(mongo.get_db())
        return self._repo

    def list(self, block: Optional[str] = None, search: Optional[str] = None, page: int = 1, per_page: int = 20) -> Tuple[List[House], int, int, int]:
        """List houses with pagination and search. Returns (items, page, total_pages, total)."""
        query = {}
        if block:
            query["block"] = block
        if search:
            query["$or"] = [
                {"block": {"$regex": search, "$options": "i"}},
                {"houseNumber": {"$regex": search, "$options": "i"}},
                {"street": {"$regex": search, "$options": "i"}},
                {"addressNote": {"$regex": search, "$options": "i"}},
            ]
        total = self.repo.count(query)
        total_pages = max(1, (total + per_page - 1) // per_page)
        if page < 1:
            page = 1
        items = self.repo.find_many(
            filter=query,
            sort=[("block", 1), ("houseNumber", 1)],
            skip=(page - 1) * per_page,
            limit=per_page,
        )
        return items, page, total_pages, total

    def find_by_id(self, house_id: str) -> Optional[House]:
        """Get a single house by ID."""
        return self.repo.find_by_id(house_id)

    def create(self, block: str, house_number: str, street: str = "",
               status: str = "vacant", address_note: str = "",
               latitude: float = 0.0, longitude: float = 0.0) -> House:
        """Create a new house and return it."""
        entity = House(
            block=block,
            house_number=house_number,
            street=street,
            status=status,
            address_note=address_note,
            latitude=latitude,
            longitude=longitude,
        )
        house_id = self.repo.create(entity)
        return self.repo.find_by_id(house_id)

    def update(self, house_id: str, block: str, house_number: str, street: str = "",
               status: str = "occupied", address_note: str = "",
               latitude: float = 0.0, longitude: float = 0.0) -> Optional[House]:
        """Update a house. Returns updated house or None if not found."""
        existing = self.repo.find_by_id(house_id)
        if not existing:
            return None
        update_fields = {
            "block": block,
            "houseNumber": house_number,
            "street": street,
            "status": status,
            "addressNote": address_note,
            "latitude": latitude,
            "longitude": longitude,
        }
        # Only include block/houseNumber if changed (avoid unique index conflict on self-update)
        if block == existing.block and house_number == existing.house_number:
            update_fields.pop("block")
            update_fields.pop("houseNumber")
        self.repo.update_by_id(house_id, update_fields)
        return self.repo.find_by_id(house_id)

    def delete(self, house_id: str) -> bool:
        """Delete a house. Returns True if deleted, False if not found."""
        existing = self.repo.find_by_id(house_id)
        if not existing:
            return False
        return self.repo.delete_by_id(house_id)

    def serialize(self, house: House) -> dict:
        """Serialize house entity to dict (for API response or template)."""
        return {
            "id": house.id,
            "block": house.block,
            "street": house.street,
            "house_number": house.house_number,
            "status": house.status,
            "latitude": house.latitude,
            "longitude": house.longitude,
            "address_note": house.address_note,
        }


# Singleton instance
house_usecase = HouseUsecase()

"""
Family Usecase - shared business logic for families.
Used by both API controller and Web admin panel.
"""

from typing import List, Optional, Tuple

from entities.family import Family


class FamilyUsecase:
    def __init__(self):
        self._repo = None

    @property
    def repo(self):
        if self._repo is None:
            from drivers.mongo.connection import Mongo
            from repositories.family import FamilyRepository
            mongo = Mongo()
            self._repo = FamilyRepository(mongo.get_db())
        return self._repo

    def list(self, search: Optional[str] = None, page: int = 1, per_page: int = 20) -> Tuple[List[Family], int, int, int]:
        """List families with pagination and search. Returns (items, page, total_pages, total)."""
        query = {}
        if search:
            query["$or"] = [
                {"headName": {"$regex": search, "$options": "i"}},
                {"headPhone": {"$regex": search, "$options": "i"}},
            ]
        total = self.repo.count(query)
        total_pages = max(1, (total + per_page - 1) // per_page)
        if page < 1:
            page = 1
        items = self.repo.find_many(
            filter=query,
            sort=[("headName", 1)],
            skip=(page - 1) * per_page,
            limit=per_page,
        )
        return items, page, total_pages, total

    def find_by_id(self, family_id: str) -> Optional[Family]:
        """Get a single family by ID."""
        return self.repo.find_by_id(family_id)

    def create(self, head_name: str, head_phone: str = "", head_id_number: str = "",
               house_id: str = "", total_members: int = 1, status: str = "active",
               members: list = None) -> Family:
        """Create a new family and return it."""
        entity = Family(
            head_name=head_name,
            head_phone=head_phone,
            head_id_number=head_id_number,
            house_id=house_id,
            total_members=total_members,
            status=status,
            members=members or [],
        )
        family_id = self.repo.create(entity)
        return self.repo.find_by_id(family_id)

    def update(self, family_id: str, head_name: str = "", head_phone: str = "",
               head_id_number: str = "", house_id: str = "",
               total_members: int = 1, status: str = "active",
               members: list = None) -> Optional[Family]:
        """Update a family. Returns updated family or None if not found."""
        existing = self.repo.find_by_id(family_id)
        if not existing:
            return None
        update_fields = {
            "headName": head_name,
            "headPhone": head_phone,
            "headIdNumber": head_id_number,
            "houseId": house_id,
            "totalMembers": total_members,
            "status": status,
        }
        if members is not None:
            update_fields["members"] = members
        self.repo.update_by_id(family_id, update_fields)
        return self.repo.find_by_id(family_id)

    def delete(self, family_id: str) -> bool:
        """Delete a family. Returns True if deleted, False if not found."""
        existing = self.repo.find_by_id(family_id)
        if not existing:
            return False
        return self.repo.delete_by_id(family_id)

    def serialize(self, family: Family) -> dict:
        """Serialize family entity to dict."""
        return {
            "id": family.id,
            "head_name": family.head_name,
            "head_phone": family.head_phone,
            "head_id_number": family.head_id_number,
            "house_id": family.house_id,
            "total_members": family.total_members,
            "status": family.status,
            "members": family.members if hasattr(family, 'members') else [],
        }


# Singleton instance
family_usecase = FamilyUsecase()

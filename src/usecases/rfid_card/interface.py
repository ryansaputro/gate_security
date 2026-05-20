"""
RFID Card Usecase - shared business logic for RFID cards.
Used by both API controller and Web admin panel.
"""

from typing import List, Optional, Tuple

from entities.rfid_card import RfidCard


class RfidCardUsecase:
    def __init__(self):
        self._repo = None

    @property
    def repo(self):
        if self._repo is None:
            from drivers.mongo.connection import Mongo
            from repositories.rfid_card import RfidCardRepository
            mongo = Mongo()
            self._repo = RfidCardRepository(mongo.get_db())
        return self._repo

    def list(self, search: Optional[str] = None, page: int = 1, per_page: int = 20) -> Tuple[List[RfidCard], int, int, int]:
        """List RFID cards with pagination and search. Returns (items, page, total_pages, total)."""
        query = {}
        if search:
            query["$or"] = [
                {"cardUid": {"$regex": search, "$options": "i"}},
                {"holderName": {"$regex": search, "$options": "i"}},
            ]
        total = self.repo.count(query)
        total_pages = max(1, (total + per_page - 1) // per_page)
        if page < 1:
            page = 1
        items = self.repo.find_many(
            filter=query,
            sort=[("cardUid", 1)],
            skip=(page - 1) * per_page,
            limit=per_page,
        )
        return items, page, total_pages, total

    def find_by_id(self, card_id: str) -> Optional[RfidCard]:
        """Get a single RFID card by ID."""
        return self.repo.find_by_id(card_id)

    def create(self, card_uid: str, holder_name: str = "", card_type: str = "resident",
               family_id: str = "", is_active: bool = True) -> RfidCard:
        """Create a new RFID card and return it."""
        entity = RfidCard(
            card_uid=card_uid.upper(),
            holder_name=holder_name,
            card_type=card_type,
            family_id=family_id,
            is_active=is_active,
        )
        card_id = self.repo.create(entity)
        return self.repo.find_by_id(card_id)

    def update(self, card_id: str, card_uid: str = "", holder_name: str = "",
               card_type: str = "resident", family_id: str = "",
               is_active: bool = True) -> Optional[RfidCard]:
        """Update an RFID card. Returns updated card or None if not found."""
        existing = self.repo.find_by_id(card_id)
        if not existing:
            return None
        update_fields = {
            "cardUid": card_uid.upper(),
            "holderName": holder_name,
            "cardType": card_type,
            "familyId": family_id,
            "isActive": is_active,
        }
        self.repo.update_by_id(card_id, update_fields)
        return self.repo.find_by_id(card_id)

    def delete(self, card_id: str) -> bool:
        """Delete an RFID card. Returns True if deleted, False if not found."""
        existing = self.repo.find_by_id(card_id)
        if not existing:
            return False
        return self.repo.delete_by_id(card_id)

    def serialize(self, card: RfidCard) -> dict:
        """Serialize RFID card entity to dict."""
        return {
            "id": card.id,
            "card_uid": card.card_uid,
            "family_id": card.family_id,
            "holder_name": card.holder_name,
            "card_type": card.card_type,
            "is_active": card.is_active,
            "blocked_reason": card.blocked_reason,
            "last_used_at": card.last_used_at,
        }


# Singleton instance
rfid_card_usecase = RfidCardUsecase()

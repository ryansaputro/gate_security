from datetime import datetime
from typing import List
from repositories.base import BaseRepository
from models import rfid_card as rfid_model


class RfidCardRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, rfid_model.COLLECTION_NAME, rfid_model)

    def find_by_uid(self, card_uid: str):
        return self.find_one({"cardUid": card_uid})

    def find_by_family_id(self, family_id: str) -> List:
        return self.find_many({"familyId": family_id, "isActive": True})

    def update_last_used(self, id: str) -> bool:
        return self.update_by_id(id, {"lastUsedAt": datetime.now()})

    def block_card(self, id: str, reason: str) -> bool:
        return self.update_by_id(id, {
            "isActive": False,
            "blockedReason": reason,
        })

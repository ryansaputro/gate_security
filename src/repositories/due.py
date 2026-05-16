from typing import List
from repositories.base import BaseRepository
from models import due as due_model


class DueRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, due_model.COLLECTION_NAME, due_model)

    def find_unpaid_by_family(self, family_id: str) -> List:
        return self.find_many({
            "familyId": family_id,
            "status": {"$in": ["unpaid", "overdue"]}
        }, sort=[("period", -1)])

    def find_by_period(self, family_id: str, period: str):
        return self.find_one({"familyId": family_id, "period": period})

    def has_unpaid_dues(self, family_id: str) -> bool:
        return self.count({
            "familyId": family_id,
            "status": {"$in": ["unpaid", "overdue"]}
        }) > 0

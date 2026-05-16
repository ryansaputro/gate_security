from repositories.base import BaseRepository
from models import family as family_model


class FamilyRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, family_model.COLLECTION_NAME, family_model)

    def find_by_house_id(self, house_id: str):
        return self.find_one({"houseId": house_id})

    def find_active(self):
        return self.find_many({"status": "active"})

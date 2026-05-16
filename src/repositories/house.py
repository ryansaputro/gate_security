from repositories.base import BaseRepository
from models import house as house_model


class HouseRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, house_model.COLLECTION_NAME, house_model)

    def find_by_block(self, block: str):
        return self.find_many({"block": block})

    def find_by_block_and_number(self, block: str, house_number: str):
        return self.find_one({"block": block, "houseNumber": house_number})

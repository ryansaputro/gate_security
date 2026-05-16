from typing import List
from repositories.base import BaseRepository
from models import master_data as master_model


class MasterDataRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, master_model.COLLECTION_NAME, master_model)

    def find_by_type(self, type: str) -> List:
        return self.find_many({"type": type, "isActive": True}, sort=[("sortOrder", 1)])

    def find_by_code(self, type: str, code: str):
        return self.find_one({"type": type, "code": code})

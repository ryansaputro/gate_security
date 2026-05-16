from repositories.base import BaseRepository
from models import setting as setting_model


class SettingRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, setting_model.COLLECTION_NAME, setting_model)

    def get_value(self, key: str, default: str = "") -> str:
        entity = self.find_one({"key": key})
        return entity.value if entity else default

    def set_value(self, key: str, value: str, updated_by: str = "system") -> bool:
        result = self.collection.update_one(
            {"key": key},
            {"$set": {"value": value, "updatedBy": updated_by}},
            upsert=True
        )
        return result.acknowledged

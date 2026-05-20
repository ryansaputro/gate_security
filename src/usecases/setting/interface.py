"""
Setting Usecase - shared business logic for system settings.
"""

from datetime import datetime
from typing import List, Optional

from entities.setting import Setting


class SettingUsecase:
    def __init__(self):
        self._repo = None

    @property
    def repo(self):
        if self._repo is None:
            from drivers.mongo.connection import Mongo
            from repositories.setting import SettingRepository
            mongo = Mongo()
            self._repo = SettingRepository(mongo.get_db())
        return self._repo

    def list(self) -> List[Setting]:
        """List all settings (no pagination, small collection)."""
        return self.repo.find_many(
            filter={},
            sort=[("category", 1), ("key", 1)],
            limit=100,
        )

    def find_by_id(self, setting_id: str) -> Optional[Setting]:
        """Get a single setting by ID."""
        return self.repo.find_by_id(setting_id)

    def get_value(self, key: str, default: str = "") -> str:
        """Get setting value by key."""
        settings = self.repo.find_many(filter={"key": key}, limit=1)
        if settings:
            return settings[0].value
        return default

    def create(self, key: str, value: str = "", category: str = "general",
               description: str = "") -> Setting:
        """Create a new setting."""
        entity = Setting(
            key=key,
            value=value,
            category=category,
            description=description,
        )
        setting_id = self.repo.create(entity)
        return self.repo.find_by_id(setting_id)

    def update(self, setting_id: str, value: str = "", category: str = "",
               description: str = "", key: str = "") -> Optional[Setting]:
        """Update a setting. Returns updated setting or None if not found."""
        existing = self.repo.find_by_id(setting_id)
        if not existing:
            return None
        update_fields = {"value": value, "updatedAt": datetime.now()}
        if category:
            update_fields["category"] = category
        if description:
            update_fields["description"] = description
        if key:
            update_fields["key"] = key
        self.repo.update_by_id(setting_id, update_fields)
        return self.repo.find_by_id(setting_id)

    def delete(self, setting_id: str) -> bool:
        """Delete a setting."""
        existing = self.repo.find_by_id(setting_id)
        if not existing:
            return False
        return self.repo.delete_by_id(setting_id)

    def serialize(self, setting: Setting) -> dict:
        """Serialize setting entity to dict."""
        return {
            "id": setting.id,
            "key": setting.key,
            "value": setting.value,
            "category": setting.category,
            "description": setting.description,
        }


# Singleton instance
setting_usecase = SettingUsecase()

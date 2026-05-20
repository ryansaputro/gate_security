"""
Setting Usecase - shared business logic for system settings.
No search, no pagination (small collection). List all, find_by_id, update (value only).
"""

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
            sort=[("category", 1)],
            limit=100,
        )

    def find_by_id(self, setting_id: str) -> Optional[Setting]:
        """Get a single setting by ID."""
        return self.repo.find_by_id(setting_id)

    def update(self, setting_id: str, value: str) -> Optional[Setting]:
        """Update a setting value. Returns updated setting or None if not found."""
        existing = self.repo.find_by_id(setting_id)
        if not existing:
            return None
        self.repo.update_by_id(setting_id, {"value": value})
        return self.repo.find_by_id(setting_id)

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

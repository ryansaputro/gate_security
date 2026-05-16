"""
Setting Controller Interface.
"""

from drivers.mongo.connection import Mongo
from repositories.setting import SettingRepository


class SettingController:
    def _get_repo(self) -> SettingRepository:
        mongo = Mongo()
        return SettingRepository(mongo.get_db())


from interfaces.http.controllers.v1.setting.list import list_settings  # noqa
from interfaces.http.controllers.v1.setting.get import get_setting  # noqa
from interfaces.http.controllers.v1.setting.upsert import upsert_setting  # noqa

SettingController.list_settings = list_settings
SettingController.get_setting = get_setting
SettingController.upsert_setting = upsert_setting

controller = SettingController()

"""
Access Log Controller Interface.
"""

from drivers.mongo.connection import Mongo
from repositories.access_log import AccessLogRepository


class AccessLogController:
    def _get_repo(self) -> AccessLogRepository:
        mongo = Mongo()
        return AccessLogRepository(mongo.get_db())


from interfaces.http.controllers.v1.access_log.list import list_recent  # noqa
from interfaces.http.controllers.v1.access_log.by_plate import by_plate  # noqa

AccessLogController.list_recent = list_recent
AccessLogController.by_plate = by_plate

controller = AccessLogController()

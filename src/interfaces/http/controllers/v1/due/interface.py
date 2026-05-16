"""
Due (Iuran) Controller Interface.
"""

from drivers.mongo.connection import Mongo
from repositories.due import DueRepository


class DueController:
    def _get_repo(self) -> DueRepository:
        mongo = Mongo()
        return DueRepository(mongo.get_db())


from interfaces.http.controllers.v1.due.list import list_unpaid  # noqa
from interfaces.http.controllers.v1.due.create import create_due  # noqa
from interfaces.http.controllers.v1.due.pay import pay_due  # noqa

DueController.list_unpaid = list_unpaid
DueController.create_due = create_due
DueController.pay_due = pay_due

controller = DueController()

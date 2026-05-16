"""
Master Data Controller Interface.
"""

from drivers.mongo.connection import Mongo
from repositories.master_data import MasterDataRepository


class MasterDataController:
    def _get_repo(self) -> MasterDataRepository:
        mongo = Mongo()
        return MasterDataRepository(mongo.get_db())


from interfaces.http.controllers.v1.master_data.list import list_by_type  # noqa
from interfaces.http.controllers.v1.master_data.create import create_master_data  # noqa
from interfaces.http.controllers.v1.master_data.delete import delete_master_data  # noqa

MasterDataController.list_by_type = list_by_type
MasterDataController.create_master_data = create_master_data
MasterDataController.delete_master_data = delete_master_data

controller = MasterDataController()

"""
Family Controller Interface.
"""

from drivers.mongo.connection import Mongo
from repositories.family import FamilyRepository


class FamilyController:
    def _get_repo(self) -> FamilyRepository:
        mongo = Mongo()
        return FamilyRepository(mongo.get_db())


from interfaces.http.controllers.v1.family.list import list_families  # noqa
from interfaces.http.controllers.v1.family.detail import get_family  # noqa
from interfaces.http.controllers.v1.family.create import create_family  # noqa
from interfaces.http.controllers.v1.family.update import update_family  # noqa
from interfaces.http.controllers.v1.family.delete import delete_family  # noqa

FamilyController.list_families = list_families
FamilyController.get_family = get_family
FamilyController.create_family = create_family
FamilyController.update_family = update_family
FamilyController.delete_family = delete_family

controller = FamilyController()

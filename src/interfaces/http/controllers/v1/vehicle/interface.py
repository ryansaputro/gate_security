"""
Vehicle Controller Interface.
"""

from drivers.mongo.connection import Mongo
from repositories.vehicle import VehicleRepository


class VehicleController:
    def _get_repo(self) -> VehicleRepository:
        mongo = Mongo()
        return VehicleRepository(mongo.get_db())


from interfaces.http.controllers.v1.vehicle.list import list_vehicles  # noqa
from interfaces.http.controllers.v1.vehicle.detail import get_vehicle  # noqa
from interfaces.http.controllers.v1.vehicle.get_by_plate import get_by_plate  # noqa
from interfaces.http.controllers.v1.vehicle.create import create_vehicle  # noqa

VehicleController.list_vehicles = list_vehicles
VehicleController.get_vehicle = get_vehicle
VehicleController.get_by_plate = get_by_plate
VehicleController.create_vehicle = create_vehicle

controller = VehicleController()

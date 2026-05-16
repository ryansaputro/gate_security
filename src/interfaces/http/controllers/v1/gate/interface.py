"""
Gate Controller Interface (mirrors basecode-golang controllers/v1/user/interface.go).
"""

from drivers.mongo.connection import Mongo
from repositories.vehicle import VehicleRepository
from repositories.rfid_card import RfidCardRepository
from repositories.access_log import AccessLogRepository
from repositories.due import DueRepository
from repositories.setting import SettingRepository
from usecases.gate.interface import GateUsecase

# Import method attachments
import usecases.gate.validate_rfid  # noqa: F401
import usecases.gate.validate_plate  # noqa: F401
import usecases.gate.log_access  # noqa: F401


class GateController:
    def _get_usecase(self) -> GateUsecase:
        mongo = Mongo()
        db = mongo.get_db()
        return GateUsecase(
            vehicle_repo=VehicleRepository(db),
            rfid_repo=RfidCardRepository(db),
            access_log_repo=AccessLogRepository(db),
            due_repo=DueRepository(db),
            setting_repo=SettingRepository(db),
        )


# Import methods
from interfaces.http.controllers.v1.gate.validate_rfid import validate_rfid  # noqa
from interfaces.http.controllers.v1.gate.validate_plate import validate_plate  # noqa

GateController.validate_rfid = validate_rfid
GateController.validate_plate = validate_plate

controller = GateController()

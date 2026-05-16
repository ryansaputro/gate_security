"""
Gate Usecase Interface (mirrors basecode-golang usecases/{domain}/interface.go).
"""

from dataclasses import dataclass
from typing import Optional

from repositories.vehicle import VehicleRepository
from repositories.rfid_card import RfidCardRepository
from repositories.access_log import AccessLogRepository
from repositories.due import DueRepository
from repositories.setting import SettingRepository


@dataclass
class ValidationResult:
    granted: bool
    method: str  # rfid | plate_ocr | manual
    family_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    plate_detected: str = ""
    confidence: float = 0.0
    reason: str = ""
    gate_mode: str = ""


class GateUsecase:
    def __init__(
        self,
        vehicle_repo: VehicleRepository,
        rfid_repo: RfidCardRepository,
        access_log_repo: AccessLogRepository,
        due_repo: DueRepository,
        setting_repo: SettingRepository,
    ):
        self.vehicle_repo = vehicle_repo
        self.rfid_repo = rfid_repo
        self.access_log_repo = access_log_repo
        self.due_repo = due_repo
        self.setting_repo = setting_repo

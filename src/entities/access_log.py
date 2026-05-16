from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class AccessLog:
    id: Optional[str] = None
    gate_id: str = ""
    direction: str = ""  # entry | exit
    method: str = ""  # rfid | plate_ocr | manual | guest_pass
    rfid_card_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    plate_detected: str = ""
    plate_confidence: float = 0.0
    family_id: Optional[str] = None
    is_resident: bool = False
    validation_result: str = ""  # granted | denied_unpaid | denied_unknown | denied_expired
    denied_reason: str = ""
    photo_url: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

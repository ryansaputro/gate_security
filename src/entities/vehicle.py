from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Vehicle:
    id: Optional[str] = None
    family_id: str = ""
    plate_number: str = ""  # "B 1234 XYZ"
    plate_number_normalized: str = ""  # "B1234XYZ"
    type: str = ""  # car | motorcycle
    brand: str = ""
    model: str = ""
    color: str = ""
    year: int = 0
    stnk_expiry: Optional[datetime] = None
    photo_url: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

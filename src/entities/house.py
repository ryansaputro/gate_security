from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class House:
    id: Optional[str] = None
    block: str = ""
    street: str = ""
    house_number: str = ""
    head_of_family_id: Optional[str] = None
    status: str = "occupied"  # occupied | vacant | rented
    latitude: float = 0.0
    longitude: float = 0.0
    address_note: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

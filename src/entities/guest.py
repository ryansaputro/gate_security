from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Guest:
    id: Optional[str] = None
    visiting_house_id: str = ""
    visiting_family_id: str = ""
    guest_name: str = ""
    guest_phone: str = ""
    guest_id_number: str = ""
    purpose: str = ""  # visit | delivery | service | contractor | other
    vehicle_plate: str = ""
    vehicle_type: str = ""  # car | motorcycle | none
    entry_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None
    entry_gate: str = ""
    exit_gate: str = ""
    entry_photo_url: str = ""
    approved_by: str = ""  # resident | security
    status: str = "inside"  # inside | exited | expired
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)

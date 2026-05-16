from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class RfidCard:
    id: Optional[str] = None
    card_uid: str = ""  # hardware UID e.g. "A1B2C3D4"
    family_id: str = ""
    holder_name: str = ""
    vehicle_ids: List[str] = field(default_factory=list)
    card_type: str = "resident"  # resident | temporary | master
    is_active: bool = True
    blocked_reason: str = ""  # unpaid_dues | lost | expired
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class FamilyMember:
    name: str = ""
    relation: str = ""  # wife | child | parent | sibling | other
    phone: str = ""
    id_number: str = ""
    birth_date: Optional[datetime] = None
    is_active: bool = True


@dataclass
class Family:
    id: Optional[str] = None
    house_id: str = ""
    head_name: str = ""
    head_phone: str = ""
    head_id_number: str = ""
    members: List[FamilyMember] = field(default_factory=list)
    total_members: int = 0
    move_in_date: Optional[datetime] = None
    status: str = "active"  # active | moved_out
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

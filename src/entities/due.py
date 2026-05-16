from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Due:
    id: Optional[str] = None
    family_id: str = ""
    house_id: str = ""
    period: str = ""  # "2026-05"
    year: int = 0
    month: int = 0
    type: str = ""  # monthly | security | cleaning | parking | other
    amount: int = 0
    paid_amount: int = 0
    status: str = "unpaid"  # paid | unpaid | partial | overdue
    paid_at: Optional[datetime] = None
    payment_method: str = ""  # cash | transfer | qris
    receipt_number: str = ""
    collector_name: str = ""
    due_date: Optional[datetime] = None
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

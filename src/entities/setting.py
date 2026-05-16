from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Setting:
    id: Optional[str] = None
    key: str = ""  # gate_mode, dues_block_enabled, etc.
    value: str = ""
    category: str = ""  # gate | dues | notification | general
    description: str = ""
    updated_by: str = ""
    updated_at: datetime = field(default_factory=datetime.now)

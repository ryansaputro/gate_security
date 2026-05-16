from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class MasterData:
    id: Optional[str] = None
    type: str = ""  # facility | vehicle_brand | gate | due_type | block
    code: str = ""
    name: str = ""
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    sort_order: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

"""
Master Data serializers.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class MasterDataCreate(BaseModel):
    type: str = Field(..., example="vehicle_brand")
    code: str = Field(..., example="TOYOTA")
    name: str = Field(..., example="Toyota")
    description: str = Field("", example="Toyota Motor Corporation")
    metadata: Dict[str, Any] = {}
    sort_order: int = Field(0, example=1)

"""
RFID Card serializers.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class RfidCardCreate(BaseModel):
    card_uid: str = Field(..., example="A1B2C3D4")
    family_id: str = Field(..., example="60f1a...")
    holder_name: str = Field(..., example="John Doe")
    vehicle_ids: List[str] = []
    card_type: str = Field("resident", example="resident")


class RfidCardBlock(BaseModel):
    card_id: str = Field(..., example="60f1a...")
    reason: str = Field(..., example="unpaid_dues")

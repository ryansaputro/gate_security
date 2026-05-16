"""
Gate validation serializers.
"""

from pydantic import BaseModel, Field


class RfidValidateRequest(BaseModel):
    card_uid: str = Field(..., example="A1B2C3D4")
    gate_id: str = Field(..., example="gate_1")
    direction: str = Field(..., example="entry")


class PlateValidateRequest(BaseModel):
    plate_detected: str = Field(..., example="B 1234 XYZ")
    confidence: float = Field(..., example=0.85)
    gate_id: str = Field(..., example="gate_1")
    direction: str = Field(..., example="entry")

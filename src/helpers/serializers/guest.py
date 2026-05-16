"""
Guest serializers.
"""

from pydantic import BaseModel, Field


class GuestCreate(BaseModel):
    visiting_house_id: str = Field(..., example="60f1a...")
    guest_name: str = Field(..., example="Ahmad")
    guest_phone: str = Field("", example="+6281234567892")
    purpose: str = Field(..., example="visit")
    vehicle_plate: str = Field("", example="D 5678 ABC")
    vehicle_type: str = Field("none", example="car")


class GuestExitRequest(BaseModel):
    guest_id: str = Field(..., example="60f1a...")
    exit_gate: str = Field(..., example="gate_1")

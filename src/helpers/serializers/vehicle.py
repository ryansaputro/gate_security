"""
Vehicle serializers.
"""

from pydantic import BaseModel, Field


class VehicleCreate(BaseModel):
    family_id: str = Field(..., example="60f1a...")
    plate_number: str = Field(..., example="B 1234 XYZ")
    type: str = Field(..., example="car")
    brand: str = Field("", example="Toyota")
    model: str = Field("", example="Avanza")
    color: str = Field("", example="Silver")
    year: int = Field(0, example=2020)

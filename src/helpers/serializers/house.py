"""
House serializers.
"""

from pydantic import BaseModel, Field


class HouseCreate(BaseModel):
    block: str = Field(..., example="A")
    street: str = Field("", example="Jalan Melati")
    house_number: str = Field(..., example="12")
    status: str = Field("occupied", example="occupied")
    latitude: float = Field(0.0)
    longitude: float = Field(0.0)
    address_note: str = Field("", example="Dekat taman")

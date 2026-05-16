"""
Due (Iuran) serializers.
"""

from pydantic import BaseModel, Field


class DueCreate(BaseModel):
    family_id: str = Field(..., example="60f1a...")
    house_id: str = Field(..., example="60f1a...")
    period: str = Field(..., example="2026-05")
    type: str = Field(..., example="monthly")
    amount: int = Field(..., example=150000)


class DuePayRequest(BaseModel):
    due_id: str = Field(..., example="60f1a...")
    paid_amount: int = Field(..., example=150000)
    payment_method: str = Field(..., example="transfer")
    collector_name: str = Field("", example="Pak RT")

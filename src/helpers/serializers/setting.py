"""
Setting serializers.
"""

from pydantic import BaseModel, Field


class SettingUpsert(BaseModel):
    key: str = Field(..., example="gate_mode")
    value: str = Field(..., example="rfid_primary")
    category: str = Field("", example="gate")
    description: str = Field("", example="Primary gate validation method")

"""
Event serializers.
"""

from typing import Optional
from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    title: str = Field(..., example="Rapat RT Bulanan")
    description: str = Field("", example="Agenda: iuran, keamanan")
    type: str = Field(..., example="meeting")
    location: str = Field("", example="Balai Warga")
    start_date: Optional[str] = Field(None, example="2026-06-01T19:00:00")
    end_date: Optional[str] = Field(None, example="2026-06-01T21:00:00")
    organizer: str = Field("", example="Pak RT")
    target_audience: str = Field("all", example="all")
    is_mandatory: bool = False

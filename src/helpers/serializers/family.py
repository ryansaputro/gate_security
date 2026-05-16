"""
Family serializers.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class FamilyMemberSchema(BaseModel):
    name: str = Field(..., example="Jane Doe")
    relation: str = Field(..., example="wife")
    phone: str = Field("", example="+6281234567891")
    id_number: str = Field("", example="3201xxxxxxxxxxxx")


class FamilyCreate(BaseModel):
    house_id: str = Field(..., example="60f1a...")
    head_name: str = Field(..., example="John Doe")
    head_phone: str = Field("", example="+6281234567890")
    head_id_number: str = Field("", example="3201xxxxxxxxxxxx")
    members: List[FamilyMemberSchema] = []


class FamilyUpdate(BaseModel):
    head_name: Optional[str] = None
    head_phone: Optional[str] = None
    members: Optional[List[FamilyMemberSchema]] = None
    status: Optional[str] = None

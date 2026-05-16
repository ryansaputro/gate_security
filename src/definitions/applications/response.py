"""
Standard response format (mirrors basecode-golang SuccessResponse).
"""

from typing import Any, Optional
from pydantic import BaseModel


class Meta(BaseModel):
    page: int = 1
    per_page: int = 50
    total_page: int = 0
    total: int = 0


class SuccessResponse(BaseModel):
    status: bool = True
    message: str = "OK"
    meta: Optional[Meta] = None
    data: Any = None

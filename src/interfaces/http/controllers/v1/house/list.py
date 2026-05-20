"""
House Controller - List houses.
"""

from typing import Optional
from definitions.applications.response import SuccessResponse


def list_houses(self, block: Optional[str] = None, skip: int = 0, limit: int = 50) -> SuccessResponse:
    """List all houses, optionally filter by block."""
    page = (skip // limit) + 1 if limit > 0 else 1
    houses, _, _, _ = self.uc.list(block=block, page=page, per_page=limit)
    return SuccessResponse(data=[self.uc.serialize(h) for h in houses])

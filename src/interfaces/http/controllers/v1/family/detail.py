"""
Family Controller - Get family detail.
"""

from fastapi import HTTPException
from definitions.applications.response import SuccessResponse


def get_family(self, family_id: str) -> SuccessResponse:
    """Get family by ID."""
    repo = self._get_repo()
    f = repo.find_by_id(family_id)
    if not f:
        raise HTTPException(status_code=404, detail="Family not found")
    return SuccessResponse(data={
        "id": f.id,
        "house_id": f.house_id,
        "head_name": f.head_name,
        "head_phone": f.head_phone,
        "head_id_number": f.head_id_number,
        "members": [{"name": m.name, "relation": m.relation, "phone": m.phone} for m in f.members],
        "total_members": f.total_members,
        "status": f.status,
    })

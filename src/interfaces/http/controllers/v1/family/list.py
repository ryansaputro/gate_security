"""
Family Controller - List families.
"""

from definitions.applications.response import SuccessResponse


def list_families(self, status: str = "active", skip: int = 0, limit: int = 50) -> SuccessResponse:
    """List families, optionally filter by status."""
    repo = self._get_repo()
    if status:
        families = repo.find_many({"status": status}, skip=skip, limit=limit)
    else:
        families = repo.find_many(skip=skip, limit=limit)
    return SuccessResponse(data=[{
        "id": f.id,
        "house_id": f.house_id,
        "head_name": f.head_name,
        "head_phone": f.head_phone,
        "total_members": f.total_members,
        "status": f.status,
    } for f in families])

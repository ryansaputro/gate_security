"""
Master Data Controller - List by type.
"""

from definitions.applications.response import SuccessResponse


def list_by_type(self, type: str) -> SuccessResponse:
    """List master data by type (e.g. vehicle_brand, gate, block)."""
    repo = self._get_repo()
    items = repo.find_by_type(type)
    return SuccessResponse(data=[{
        "id": i.id,
        "type": i.type,
        "code": i.code,
        "name": i.name,
        "description": i.description,
        "metadata": i.metadata,
        "sort_order": i.sort_order,
    } for i in items])

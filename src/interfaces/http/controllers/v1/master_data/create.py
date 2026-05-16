"""
Master Data Controller - Create master data.
"""

from helpers.serializers.master_data import MasterDataCreate
from definitions.applications.response import SuccessResponse
from entities.master_data import MasterData


def create_master_data(self, body: MasterDataCreate) -> SuccessResponse:
    """Create a new master data entry."""
    repo = self._get_repo()
    entity = MasterData(
        type=body.type,
        code=body.code,
        name=body.name,
        description=body.description,
        metadata=body.metadata,
        sort_order=body.sort_order,
    )
    mid = repo.create(entity)
    m = repo.find_by_id(mid)
    return SuccessResponse(data={"id": m.id, "type": m.type, "code": m.code, "name": m.name})

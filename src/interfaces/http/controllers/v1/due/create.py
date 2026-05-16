"""
Due Controller - Create due.
"""

from helpers.serializers.due import DueCreate
from definitions.applications.response import SuccessResponse
from entities.due import Due


def create_due(self, body: DueCreate) -> SuccessResponse:
    """Create a new due/billing record."""
    repo = self._get_repo()
    entity = Due(
        family_id=body.family_id,
        house_id=body.house_id,
        period=body.period,
        year=int(body.period.split("-")[0]),
        month=int(body.period.split("-")[1]),
        type=body.type,
        amount=body.amount,
        status="unpaid",
    )
    did = repo.create(entity)
    due = repo.find_by_id(did)
    return SuccessResponse(data={
        "id": due.id,
        "family_id": due.family_id,
        "period": due.period,
        "amount": due.amount,
        "status": due.status,
    })

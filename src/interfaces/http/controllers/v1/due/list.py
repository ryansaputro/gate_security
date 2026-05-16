"""
Due Controller - List unpaid dues.
"""

from definitions.applications.response import SuccessResponse


def list_unpaid(self, family_id: str) -> SuccessResponse:
    """Get unpaid/overdue dues for a family."""
    repo = self._get_repo()
    dues = repo.find_unpaid_by_family(family_id)
    return SuccessResponse(data=[{
        "id": d.id,
        "family_id": d.family_id,
        "house_id": d.house_id,
        "period": d.period,
        "type": d.type,
        "amount": d.amount,
        "paid_amount": d.paid_amount,
        "status": d.status,
    } for d in dues])

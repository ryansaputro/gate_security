"""
Due Controller - Pay due.
"""

from datetime import datetime
from fastapi import HTTPException
from helpers.serializers.due import DuePayRequest
from definitions.applications.response import SuccessResponse


def pay_due(self, body: DuePayRequest) -> SuccessResponse:
    """Record payment for a due."""
    repo = self._get_repo()
    due = repo.find_by_id(body.due_id)
    if not due:
        raise HTTPException(status_code=404, detail="Due not found")

    new_paid = due.paid_amount + body.paid_amount
    status = "paid" if new_paid >= due.amount else "partial"

    repo.update_by_id(body.due_id, {
        "paidAmount": new_paid,
        "status": status,
        "paidAt": datetime.now(),
        "paymentMethod": body.payment_method,
        "collectorName": body.collector_name,
    })
    due = repo.find_by_id(body.due_id)
    return SuccessResponse(data={
        "id": due.id,
        "period": due.period,
        "amount": due.amount,
        "paid_amount": due.paid_amount,
        "status": due.status,
        "payment_method": due.payment_method,
    })

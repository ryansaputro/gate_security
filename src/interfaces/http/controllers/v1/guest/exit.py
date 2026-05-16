"""
Guest Controller - Mark guest exit.
"""

from fastapi import HTTPException
from helpers.serializers.guest import GuestExitRequest
from definitions.applications.response import SuccessResponse


def mark_guest_exit(self, body: GuestExitRequest) -> SuccessResponse:
    """Mark a guest as exited."""
    repo = self._get_repo()
    guest = repo.find_by_id(body.guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    repo.mark_exited(body.guest_id, body.exit_gate)
    guest = repo.find_by_id(body.guest_id)
    return SuccessResponse(data={
        "id": guest.id,
        "guest_name": guest.guest_name,
        "status": guest.status,
        "exit_time": guest.exit_time.isoformat() if guest.exit_time else None,
    })

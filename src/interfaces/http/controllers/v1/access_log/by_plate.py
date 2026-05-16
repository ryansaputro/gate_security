"""
Access Log Controller - Get logs by plate.
"""

from definitions.applications.response import SuccessResponse


def by_plate(self, plate: str, limit: int = 10) -> SuccessResponse:
    """Get access logs for a specific plate number."""
    repo = self._get_repo()
    logs = repo.find_by_plate(plate, limit=limit)
    return SuccessResponse(data=[{
        "id": l.id,
        "gate_id": l.gate_id,
        "direction": l.direction,
        "method": l.method,
        "plate_detected": l.plate_detected,
        "plate_confidence": l.plate_confidence,
        "validation_result": l.validation_result,
        "timestamp": l.timestamp.isoformat() if l.timestamp else None,
    } for l in logs])

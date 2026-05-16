"""
Access Log Controller - List recent logs.
"""

from definitions.applications.response import SuccessResponse


def list_recent(self, limit: int = 50) -> SuccessResponse:
    """Get recent access logs."""
    repo = self._get_repo()
    logs = repo.find_recent(limit=limit)
    return SuccessResponse(data=[_serialize(l) for l in logs])


def _serialize(log) -> dict:
    return {
        "id": log.id,
        "gate_id": log.gate_id,
        "direction": log.direction,
        "method": log.method,
        "plate_detected": log.plate_detected,
        "plate_confidence": log.plate_confidence,
        "family_id": log.family_id,
        "is_resident": log.is_resident,
        "validation_result": log.validation_result,
        "timestamp": log.timestamp.isoformat() if log.timestamp else None,
    }

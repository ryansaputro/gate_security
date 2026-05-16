"""
Log Access - Gate usecase helper method.
"""

from datetime import datetime
from entities.access_log import AccessLog
from usecases.gate.interface import GateUsecase


def _log_access(
    self: GateUsecase, gate_id: str, direction: str, method: str,
    result: str, plate: str = "", confidence: float = 0.0,
    family_id: str = None, vehicle_id: str = None
):
    log = AccessLog(
        gate_id=gate_id,
        direction=direction,
        method=method,
        plate_detected=plate,
        plate_confidence=confidence,
        family_id=family_id,
        vehicle_id=vehicle_id,
        is_resident=family_id is not None,
        validation_result=result,
        timestamp=datetime.now(),
    )
    self.access_log_repo.create(log)


GateUsecase._log_access = _log_access

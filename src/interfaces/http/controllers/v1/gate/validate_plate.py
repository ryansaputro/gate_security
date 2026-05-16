"""
Gate Controller - Validate Plate OCR endpoint.
"""

from helpers.serializers.gate import PlateValidateRequest
from definitions.applications.response import SuccessResponse


def validate_plate(self, body: PlateValidateRequest) -> SuccessResponse:
    """
    Validate gate access via license plate OCR detection.

    Flow:
    1. Check gate_mode setting
    2. Get ocr_confidence_threshold from settings
    3. Exact match plate → if found, check dues
    4. Fuzzy match (levenshtein + contains) → if found, check dues
    5. Grant / Deny
    """
    uc = self._get_usecase()
    result = uc.validate_plate(
        body.plate_detected, body.confidence, body.gate_id, body.direction
    )
    return SuccessResponse(
        status=result.granted,
        message="granted" if result.granted else result.reason,
        data={
            "granted": result.granted,
            "method": result.method,
            "gate_mode": result.gate_mode,
            "plate_detected": result.plate_detected,
            "confidence": result.confidence,
            "family_id": result.family_id,
            "vehicle_id": result.vehicle_id,
            "reason": result.reason,
        },
    )

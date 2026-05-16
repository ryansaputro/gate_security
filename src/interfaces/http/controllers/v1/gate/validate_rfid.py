"""
Gate Controller - Validate RFID endpoint.
"""

from helpers.serializers.gate import RfidValidateRequest
from definitions.applications.response import SuccessResponse


def validate_rfid(self, body: RfidValidateRequest) -> SuccessResponse:
    """
    Validate gate access via RFID card scan.

    Flow:
    1. Check gate_mode setting (rfid_only, plate_only, rfid_primary, both_required)
    2. Find card → registered?
    3. Card active? → not blocked?
    4. Card expired? → expires_at check
    5. Dues paid? → check iuran bulan lalu
    6. Grant / Deny
    """
    uc = self._get_usecase()
    result = uc.validate_rfid(body.card_uid, body.gate_id, body.direction)
    return SuccessResponse(
        status=result.granted,
        message="granted" if result.granted else result.reason,
        data={
            "granted": result.granted,
            "method": result.method,
            "gate_mode": result.gate_mode,
            "family_id": result.family_id,
            "reason": result.reason,
        },
    )

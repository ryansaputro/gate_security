"""
Validate RFID - Gate usecase method.

Flow:
1. Check setting gate_mode → apakah RFID diperbolehkan
2. Find card by UID → terdaftar?
3. Check card active → expired/blocked?
4. Check card expires_at → masih berlaku?
5. Check dues_block_enabled → kalau enabled, check iuran bulan lalu
6. Grant / Deny
"""

from datetime import datetime
from usecases.gate.interface import GateUsecase, ValidationResult


def validate_rfid(self: GateUsecase, card_uid: str, gate_id: str, direction: str) -> ValidationResult:
    """Validate access via RFID card scan."""

    # Step 1: Check gate_mode setting
    gate_mode = self.setting_repo.get_value("gate_mode", "rfid_primary")
    if gate_mode == "plate_only":
        self._log_access(gate_id, direction, "rfid", "denied_mode")
        return ValidationResult(
            granted=False, method="rfid", gate_mode=gate_mode,
            reason="Gate mode is plate_only, RFID not accepted"
        )

    # Step 2: Find card - terdaftar?
    card = self.rfid_repo.find_by_uid(card_uid)
    if not card:
        self._log_access(gate_id, direction, "rfid", "denied_unknown")
        return ValidationResult(
            granted=False, method="rfid", gate_mode=gate_mode,
            reason="Card not registered"
        )

    # Step 3: Check active - blocked?
    if not card.is_active:
        self._log_access(gate_id, direction, "rfid", "denied_blocked",
                         family_id=card.family_id)
        return ValidationResult(
            granted=False, method="rfid", gate_mode=gate_mode,
            family_id=card.family_id,
            reason=f"Card blocked: {card.blocked_reason}"
        )

    # Step 4: Check expires_at - expired?
    if card.expires_at and card.expires_at < datetime.now():
        self._log_access(gate_id, direction, "rfid", "denied_expired",
                         family_id=card.family_id)
        return ValidationResult(
            granted=False, method="rfid", gate_mode=gate_mode,
            family_id=card.family_id,
            reason="Card expired"
        )

    # Step 5: Check iuran (if dues_block_enabled)
    dues_block = self.setting_repo.get_value("dues_block_enabled", "true")
    if dues_block == "true":
        if self.due_repo.has_unpaid_dues(card.family_id):
            self._log_access(gate_id, direction, "rfid", "denied_unpaid",
                             family_id=card.family_id)
            return ValidationResult(
                granted=False, method="rfid", gate_mode=gate_mode,
                family_id=card.family_id,
                reason="Unpaid dues - please settle before access"
            )

    # Step 6: Grant access
    self.rfid_repo.update_last_used(card.id)
    self._log_access(gate_id, direction, "rfid", "granted",
                     family_id=card.family_id)
    return ValidationResult(
        granted=True, method="rfid", gate_mode=gate_mode,
        family_id=card.family_id
    )


GateUsecase.validate_rfid = validate_rfid

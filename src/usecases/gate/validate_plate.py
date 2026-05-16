"""
Validate Plate OCR - Gate usecase method.

Flow:
1. Check setting gate_mode → apakah plate diperbolehkan
2. Get ocr_confidence_threshold dari settings
3. Normalize plate → exact match dulu
4. Kalau ga exact → fuzzy match (levenshtein + contains)
5. Check dues_block_enabled → kalau enabled, check iuran
6. Grant / Deny
"""

from typing import Optional
from usecases.gate.interface import GateUsecase, ValidationResult


def validate_plate(
    self: GateUsecase, plate_detected: str, confidence: float,
    gate_id: str, direction: str
) -> ValidationResult:
    """Validate access via plate OCR detection with fuzzy matching."""

    # Step 1: Check gate_mode
    gate_mode = self.setting_repo.get_value("gate_mode", "rfid_primary")
    if gate_mode == "rfid_only":
        self._log_access(gate_id, direction, "plate_ocr", "denied_mode",
                         plate=plate_detected, confidence=confidence)
        return ValidationResult(
            granted=False, method="plate_ocr", gate_mode=gate_mode,
            plate_detected=plate_detected, confidence=confidence,
            reason="Gate mode is rfid_only, plate not accepted"
        )

    # Step 2: Get confidence threshold from settings
    threshold_str = self.setting_repo.get_value("ocr_confidence_threshold", "0.6")
    fuzzy_threshold = float(threshold_str)

    # Step 3: Normalize and exact match
    normalized = plate_detected.replace(" ", "").upper()

    vehicle = self.vehicle_repo.find_by_plate(normalized)
    if vehicle:
        return self._check_dues_and_grant(
            vehicle, gate_id, direction, plate_detected,
            confidence, gate_mode, match_type="exact"
        )

    # Step 4: Fuzzy match
    all_plates = self.vehicle_repo.find_all_active_plates()
    best_match, match_score = _fuzzy_match(normalized, all_plates, fuzzy_threshold)

    if best_match:
        vehicle = self.vehicle_repo.find_by_plate(best_match)
        if vehicle:
            return self._check_dues_and_grant(
                vehicle, gate_id, direction, plate_detected,
                confidence, gate_mode, match_type=f"fuzzy({match_score:.0%})"
            )

    # No match found
    self._log_access(gate_id, direction, "plate_ocr", "denied_unknown",
                     plate=plate_detected, confidence=confidence)
    return ValidationResult(
        granted=False, method="plate_ocr", gate_mode=gate_mode,
        plate_detected=plate_detected, confidence=confidence,
        reason="Vehicle not registered (no match found)"
    )


def _check_dues_and_grant(
    self: GateUsecase, vehicle, gate_id: str, direction: str,
    plate_detected: str, confidence: float, gate_mode: str, match_type: str
) -> ValidationResult:
    """Check dues then grant/deny."""
    # Step 5: Check iuran
    dues_block = self.setting_repo.get_value("dues_block_enabled", "true")
    if dues_block == "true":
        if self.due_repo.has_unpaid_dues(vehicle.family_id):
            self._log_access(gate_id, direction, "plate_ocr", "denied_unpaid",
                             plate=plate_detected, confidence=confidence,
                             family_id=vehicle.family_id, vehicle_id=vehicle.id)
            return ValidationResult(
                granted=False, method="plate_ocr", gate_mode=gate_mode,
                plate_detected=plate_detected, confidence=confidence,
                family_id=vehicle.family_id, vehicle_id=vehicle.id,
                reason="Unpaid dues - please settle before access"
            )

    # Step 6: Grant
    self._log_access(gate_id, direction, "plate_ocr", "granted",
                     plate=plate_detected, confidence=confidence,
                     family_id=vehicle.family_id, vehicle_id=vehicle.id)
    return ValidationResult(
        granted=True, method="plate_ocr", gate_mode=gate_mode,
        plate_detected=plate_detected, confidence=confidence,
        family_id=vehicle.family_id, vehicle_id=vehicle.id,
        reason=f"matched ({match_type})"
    )


def _fuzzy_match(detected: str, db_plates: list, threshold: float = 0.6) -> tuple:
    """
    Fuzzy match detected plate against DB plates.
    Returns (best_plate, score) or (None, 0).

    Strategies:
    1. Exact match → score 1.0
    2. Contains match → partial read "6797" in "F6797OB"
    3. Levenshtein distance → "F6797O8" vs "F6797OB"
    """
    if not detected or not db_plates:
        return None, 0.0

    best_plate = None
    best_score = 0.0

    for db_plate in db_plates:
        # Strategy 1: Exact
        if detected == db_plate:
            return db_plate, 1.0

        # Strategy 2: Contains (partial read)
        if detected in db_plate:
            score = len(detected) / len(db_plate)
            if score > best_score:
                best_score = score
                best_plate = db_plate
            continue

        # Strategy 3: Levenshtein
        distance = _levenshtein(detected, db_plate)
        max_len = max(len(detected), len(db_plate))
        score = 1 - (distance / max_len) if max_len > 0 else 0

        if score > best_score:
            best_score = score
            best_plate = db_plate

    if best_score >= threshold:
        return best_plate, best_score
    return None, 0.0


def _levenshtein(s1: str, s2: str) -> int:
    """Levenshtein edit distance."""
    if len(s1) < len(s2):
        return _levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            curr_row.append(min(prev_row[j + 1] + 1, curr_row[j] + 1, prev_row[j] + (c1 != c2)))
        prev_row = curr_row
    return prev_row[-1]


GateUsecase.validate_plate = validate_plate
GateUsecase._check_dues_and_grant = _check_dues_and_grant

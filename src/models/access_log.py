from entities.access_log import AccessLog

COLLECTION_NAME = "access_logs"


def to_document(entity: AccessLog) -> dict:
    doc = {
        "gateId": entity.gate_id,
        "direction": entity.direction,
        "method": entity.method,
        "rfidCardId": entity.rfid_card_id,
        "vehicleId": entity.vehicle_id,
        "plateDetected": entity.plate_detected,
        "plateConfidence": entity.plate_confidence,
        "familyId": entity.family_id,
        "isResident": entity.is_resident,
        "validationResult": entity.validation_result,
        "deniedReason": entity.denied_reason,
        "photoUrl": entity.photo_url,
        "timestamp": entity.timestamp,
    }
    if entity.id:
        doc["_id"] = entity.id
    return doc


def from_document(doc: dict) -> AccessLog:
    return AccessLog(
        id=str(doc.get("_id", "")),
        gate_id=doc.get("gateId", ""),
        direction=doc.get("direction", ""),
        method=doc.get("method", ""),
        rfid_card_id=doc.get("rfidCardId"),
        vehicle_id=doc.get("vehicleId"),
        plate_detected=doc.get("plateDetected", ""),
        plate_confidence=doc.get("plateConfidence", 0.0),
        family_id=doc.get("familyId"),
        is_resident=doc.get("isResident", False),
        validation_result=doc.get("validationResult", ""),
        denied_reason=doc.get("deniedReason", ""),
        photo_url=doc.get("photoUrl", ""),
        timestamp=doc.get("timestamp"),
    )

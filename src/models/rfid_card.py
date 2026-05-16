from entities.rfid_card import RfidCard

COLLECTION_NAME = "rfid_cards"


def to_document(entity: RfidCard) -> dict:
    doc = {
        "cardUid": entity.card_uid,
        "familyId": entity.family_id,
        "holderName": entity.holder_name,
        "vehicleIds": entity.vehicle_ids,
        "cardType": entity.card_type,
        "isActive": entity.is_active,
        "blockedReason": entity.blocked_reason,
        "issuedAt": entity.issued_at,
        "expiresAt": entity.expires_at,
        "lastUsedAt": entity.last_used_at,
        "createdAt": entity.created_at,
        "updatedAt": entity.updated_at,
    }
    if entity.id:
        doc["_id"] = entity.id
    return doc


def from_document(doc: dict) -> RfidCard:
    return RfidCard(
        id=str(doc.get("_id", "")),
        card_uid=doc.get("cardUid", ""),
        family_id=doc.get("familyId", ""),
        holder_name=doc.get("holderName", ""),
        vehicle_ids=doc.get("vehicleIds", []),
        card_type=doc.get("cardType", "resident"),
        is_active=doc.get("isActive", True),
        blocked_reason=doc.get("blockedReason", ""),
        issued_at=doc.get("issuedAt"),
        expires_at=doc.get("expiresAt"),
        last_used_at=doc.get("lastUsedAt"),
        created_at=doc.get("createdAt"),
        updated_at=doc.get("updatedAt"),
    )

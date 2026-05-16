from entities.guest import Guest

COLLECTION_NAME = "guests"


def to_document(entity: Guest) -> dict:
    doc = {
        "visitingHouseId": entity.visiting_house_id,
        "visitingFamilyId": entity.visiting_family_id,
        "guestName": entity.guest_name,
        "guestPhone": entity.guest_phone,
        "guestIdNumber": entity.guest_id_number,
        "purpose": entity.purpose,
        "vehiclePlate": entity.vehicle_plate,
        "vehicleType": entity.vehicle_type,
        "entryTime": entity.entry_time,
        "exitTime": entity.exit_time,
        "entryGate": entity.entry_gate,
        "exitGate": entity.exit_gate,
        "entryPhotoUrl": entity.entry_photo_url,
        "approvedBy": entity.approved_by,
        "status": entity.status,
        "notes": entity.notes,
        "createdAt": entity.created_at,
    }
    if entity.id:
        doc["_id"] = entity.id
    return doc


def from_document(doc: dict) -> Guest:
    return Guest(
        id=str(doc.get("_id", "")),
        visiting_house_id=doc.get("visitingHouseId", ""),
        visiting_family_id=doc.get("visitingFamilyId", ""),
        guest_name=doc.get("guestName", ""),
        guest_phone=doc.get("guestPhone", ""),
        guest_id_number=doc.get("guestIdNumber", ""),
        purpose=doc.get("purpose", ""),
        vehicle_plate=doc.get("vehiclePlate", ""),
        vehicle_type=doc.get("vehicleType", ""),
        entry_time=doc.get("entryTime"),
        exit_time=doc.get("exitTime"),
        entry_gate=doc.get("entryGate", ""),
        exit_gate=doc.get("exitGate", ""),
        entry_photo_url=doc.get("entryPhotoUrl", ""),
        approved_by=doc.get("approvedBy", ""),
        status=doc.get("status", "inside"),
        notes=doc.get("notes", ""),
        created_at=doc.get("createdAt"),
    )

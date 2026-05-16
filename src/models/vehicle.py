from entities.vehicle import Vehicle

COLLECTION_NAME = "vehicles"


def to_document(entity: Vehicle) -> dict:
    doc = {
        "familyId": entity.family_id,
        "plateNumber": entity.plate_number,
        "plateNumberNormalized": entity.plate_number_normalized,
        "type": entity.type,
        "brand": entity.brand,
        "model": entity.model,
        "color": entity.color,
        "year": entity.year,
        "stnkExpiry": entity.stnk_expiry,
        "photoUrl": entity.photo_url,
        "isActive": entity.is_active,
        "createdAt": entity.created_at,
        "updatedAt": entity.updated_at,
    }
    if entity.id:
        doc["_id"] = entity.id
    return doc


def from_document(doc: dict) -> Vehicle:
    return Vehicle(
        id=str(doc.get("_id", "")),
        family_id=doc.get("familyId", ""),
        plate_number=doc.get("plateNumber", ""),
        plate_number_normalized=doc.get("plateNumberNormalized", ""),
        type=doc.get("type", ""),
        brand=doc.get("brand", ""),
        model=doc.get("model", ""),
        color=doc.get("color", ""),
        year=doc.get("year", 0),
        stnk_expiry=doc.get("stnkExpiry"),
        photo_url=doc.get("photoUrl", ""),
        is_active=doc.get("isActive", True),
        created_at=doc.get("createdAt"),
        updated_at=doc.get("updatedAt"),
    )

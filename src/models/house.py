from entities.house import House

COLLECTION_NAME = "houses"


def to_document(entity: House) -> dict:
    doc = {
        "block": entity.block,
        "street": entity.street,
        "houseNumber": entity.house_number,
        "headOfFamilyId": entity.head_of_family_id,
        "status": entity.status,
        "latitude": entity.latitude,
        "longitude": entity.longitude,
        "addressNote": entity.address_note,
        "createdAt": entity.created_at,
        "updatedAt": entity.updated_at,
    }
    if entity.id:
        doc["_id"] = entity.id
    return doc


def from_document(doc: dict) -> House:
    return House(
        id=str(doc.get("_id", "")),
        block=doc.get("block", ""),
        street=doc.get("street", ""),
        house_number=doc.get("houseNumber", ""),
        head_of_family_id=doc.get("headOfFamilyId"),
        status=doc.get("status", "occupied"),
        latitude=doc.get("latitude", 0.0),
        longitude=doc.get("longitude", 0.0),
        address_note=doc.get("addressNote", ""),
        created_at=doc.get("createdAt"),
        updated_at=doc.get("updatedAt"),
    )

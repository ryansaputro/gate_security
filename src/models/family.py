from entities.family import Family, FamilyMember

COLLECTION_NAME = "families"


def _member_to_document(member: FamilyMember) -> dict:
    return {
        "name": member.name,
        "relation": member.relation,
        "phone": member.phone,
        "idNumber": member.id_number,
        "birthDate": member.birth_date,
        "isActive": member.is_active,
    }


def _member_from_document(doc: dict) -> FamilyMember:
    return FamilyMember(
        name=doc.get("name", ""),
        relation=doc.get("relation", ""),
        phone=doc.get("phone", ""),
        id_number=doc.get("idNumber", ""),
        birth_date=doc.get("birthDate"),
        is_active=doc.get("isActive", True),
    )


def to_document(entity: Family) -> dict:
    doc = {
        "houseId": entity.house_id,
        "headName": entity.head_name,
        "headPhone": entity.head_phone,
        "headIdNumber": entity.head_id_number,
        "members": [_member_to_document(m) for m in entity.members],
        "totalMembers": entity.total_members,
        "moveInDate": entity.move_in_date,
        "status": entity.status,
        "createdAt": entity.created_at,
        "updatedAt": entity.updated_at,
    }
    if entity.id:
        doc["_id"] = entity.id
    return doc


def from_document(doc: dict) -> Family:
    return Family(
        id=str(doc.get("_id", "")),
        house_id=doc.get("houseId", ""),
        head_name=doc.get("headName", ""),
        head_phone=doc.get("headPhone", ""),
        head_id_number=doc.get("headIdNumber", ""),
        members=[_member_from_document(m) for m in doc.get("members", [])],
        total_members=doc.get("totalMembers", 0),
        move_in_date=doc.get("moveInDate"),
        status=doc.get("status", "active"),
        created_at=doc.get("createdAt"),
        updated_at=doc.get("updatedAt"),
    )

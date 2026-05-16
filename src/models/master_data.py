from entities.master_data import MasterData

COLLECTION_NAME = "master_data"


def to_document(entity: MasterData) -> dict:
    doc = {
        "type": entity.type,
        "code": entity.code,
        "name": entity.name,
        "description": entity.description,
        "metadata": entity.metadata,
        "isActive": entity.is_active,
        "sortOrder": entity.sort_order,
        "createdAt": entity.created_at,
        "updatedAt": entity.updated_at,
    }
    if entity.id:
        doc["_id"] = entity.id
    return doc


def from_document(doc: dict) -> MasterData:
    return MasterData(
        id=str(doc.get("_id", "")),
        type=doc.get("type", ""),
        code=doc.get("code", ""),
        name=doc.get("name", ""),
        description=doc.get("description", ""),
        metadata=doc.get("metadata", {}),
        is_active=doc.get("isActive", True),
        sort_order=doc.get("sortOrder", 0),
        created_at=doc.get("createdAt"),
        updated_at=doc.get("updatedAt"),
    )

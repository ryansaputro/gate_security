from entities.setting import Setting

COLLECTION_NAME = "settings"


def to_document(entity: Setting) -> dict:
    doc = {
        "key": entity.key,
        "value": entity.value,
        "category": entity.category,
        "description": entity.description,
        "updatedBy": entity.updated_by,
        "updatedAt": entity.updated_at,
    }
    if entity.id:
        doc["_id"] = entity.id
    return doc


def from_document(doc: dict) -> Setting:
    return Setting(
        id=str(doc.get("_id", "")),
        key=doc.get("key", ""),
        value=doc.get("value", ""),
        category=doc.get("category", ""),
        description=doc.get("description", ""),
        updated_by=doc.get("updatedBy", ""),
        updated_at=doc.get("updatedAt"),
    )

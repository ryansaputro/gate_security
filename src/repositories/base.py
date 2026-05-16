"""
Base repository with generic CRUD operations for MongoDB.
All specific repositories inherit from this.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId


class BaseRepository:
    def __init__(self, db, collection_name: str, model_module):
        self.collection = db[collection_name]
        self.model = model_module

    def create(self, entity) -> str:
        doc = self.model.to_document(entity)
        doc.pop("_id", None)
        doc["createdAt"] = datetime.now()
        doc["updatedAt"] = datetime.now()
        result = self.collection.insert_one(doc)
        return str(result.inserted_id)

    def find_by_id(self, id: str):
        doc = self.collection.find_one({"_id": ObjectId(id)})
        if not doc:
            return None
        return self.model.from_document(doc)

    def find_one(self, filter: Dict[str, Any]):
        doc = self.collection.find_one(filter)
        if not doc:
            return None
        return self.model.from_document(doc)

    def find_many(self, filter: Dict[str, Any] = None, sort: List = None,
                  skip: int = 0, limit: int = 50) -> List:
        cursor = self.collection.find(filter or {})
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        return [self.model.from_document(doc) for doc in cursor]

    def update_by_id(self, id: str, update_fields: Dict[str, Any]) -> bool:
        update_fields["updatedAt"] = datetime.now()
        result = self.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_fields}
        )
        return result.modified_count > 0

    def delete_by_id(self, id: str) -> bool:
        result = self.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0

    def count(self, filter: Dict[str, Any] = None) -> int:
        return self.collection.count_documents(filter or {})

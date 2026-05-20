"""
Admin Usecase - shared business logic for admin users.
Uses direct pymongo (no entity/model/repo layer for admins).
"""

import hashlib
from datetime import datetime
from typing import List, Optional, Tuple

from bson import ObjectId


def _hash_password(password: str) -> str:
    """Simple SHA256 hash for passwords."""
    return hashlib.sha256(password.encode()).hexdigest()


class AdminUsecase:
    def __init__(self):
        self._db = None

    @property
    def db(self):
        if self._db is None:
            from drivers.mongo.connection import Mongo
            mongo = Mongo()
            self._db = mongo.get_db()
        return self._db

    @property
    def collection(self):
        return self.db.admins

    def list(self, search: Optional[str] = None, page: int = 1, per_page: int = 20) -> Tuple[List[dict], int, int, int]:
        """List admins with pagination and search. Returns (items, page, total_pages, total)."""
        query = {}
        if search:
            query["$or"] = [
                {"username": {"$regex": search, "$options": "i"}},
                {"name": {"$regex": search, "$options": "i"}},
            ]
        total = self.collection.count_documents(query)
        total_pages = max(1, (total + per_page - 1) // per_page)
        if page < 1:
            page = 1
        items = list(
            self.collection.find(query)
            .sort("username", 1)
            .skip((page - 1) * per_page)
            .limit(per_page)
        )
        return items, page, total_pages, total

    def find_by_id(self, admin_id: str) -> Optional[dict]:
        """Get a single admin by ID."""
        return self.collection.find_one({"_id": ObjectId(admin_id)})

    def create(self, username: str, name: str = "", password: str = "",
               role: str = "admin", is_active: bool = True) -> Optional[dict]:
        """Create a new admin. Returns None if username already exists."""
        if self.collection.find_one({"username": username}):
            return None  # duplicate
        doc = {
            "username": username,
            "name": name,
            "password_hash": _hash_password(password),
            "role": role,
            "is_active": is_active,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        result = self.collection.insert_one(doc)
        return self.collection.find_one({"_id": result.inserted_id})

    def update(self, admin_id: str, name: str = "", password: str = "",
               role: str = "admin", is_active: bool = True) -> Optional[dict]:
        """Update an admin. Returns updated admin or None if not found."""
        existing = self.find_by_id(admin_id)
        if not existing:
            return None
        update_fields = {
            "name": name,
            "role": role,
            "is_active": is_active,
            "updated_at": datetime.utcnow(),
        }
        if password:
            update_fields["password_hash"] = _hash_password(password)
        self.collection.update_one({"_id": ObjectId(admin_id)}, {"$set": update_fields})
        return self.find_by_id(admin_id)

    def delete(self, admin_id: str) -> bool:
        """Delete an admin. Returns True if deleted."""
        result = self.collection.delete_one({"_id": ObjectId(admin_id)})
        return result.deleted_count > 0

    def serialize(self, admin: dict) -> dict:
        """Serialize admin document to dict."""
        return {
            "id": str(admin.get("_id", "")),
            "username": admin.get("username", ""),
            "name": admin.get("name", ""),
            "role": admin.get("role", "admin"),
            "is_active": admin.get("is_active", True),
            "last_login_at": admin.get("last_login_at"),
        }


# Singleton instance
admin_usecase = AdminUsecase()

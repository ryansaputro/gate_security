"""
API Key Authentication Middleware.

Roles:
- admin: Full access to all endpoints
- device: Only gate validation endpoints (validate-rfid, validate-plate)

API keys stored in MongoDB `api_keys` collection.
Header: X-API-Key
"""

import os
import hashlib
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader

from drivers.mongo.connection import Mongo


API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def _hash_key(raw_key: str) -> str:
    """Hash API key with SHA-256 for storage comparison."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


def _find_api_key(raw_key: str) -> Optional[dict]:
    """Lookup API key in database."""
    mongo = Mongo()
    db = mongo.get_db()
    hashed = _hash_key(raw_key)
    return db["api_keys"].find_one({"key_hash": hashed, "is_active": True})


def require_auth(allowed_roles: list = None):
    """
    Dependency factory for role-based API key auth.

    Usage in routes:
        from fastapi import Depends
        router.get("/admin-only", dependencies=[Depends(require_auth(["admin"]))])
        router.post("/gate", dependencies=[Depends(require_auth(["admin", "device"]))])
    """
    if allowed_roles is None:
        allowed_roles = ["admin"]

    async def _verify(request: Request, api_key: str = Security(API_KEY_HEADER)):
        # Skip auth in dev if AUTH_ENABLED=false
        if os.getenv("AUTH_ENABLED", "true").lower() == "false":
            request.state.auth_role = "admin"
            request.state.auth_name = "dev-bypass"
            return

        if not api_key:
            raise HTTPException(status_code=401, detail="Missing X-API-Key header")

        key_doc = _find_api_key(api_key)
        if not key_doc:
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Check expiry
        if key_doc.get("expires_at") and key_doc["expires_at"] < datetime.now():
            raise HTTPException(status_code=401, detail="API key expired")

        # Check role
        role = key_doc.get("role", "device")
        if role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required: {allowed_roles}, got: {role}"
            )

        # Attach to request state
        request.state.auth_role = role
        request.state.auth_name = key_doc.get("name", "unknown")

        # Update last_used_at (fire and forget)
        mongo = Mongo()
        db = mongo.get_db()
        db["api_keys"].update_one(
            {"_id": key_doc["_id"]},
            {"$set": {"last_used_at": datetime.now()}}
        )

    return _verify

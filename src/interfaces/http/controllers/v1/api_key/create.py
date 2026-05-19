"""
Create API Key endpoint.
"""

import secrets
import hashlib
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, Request
from pydantic import BaseModel


class CreateKeyRequest(BaseModel):
    name: str
    role: str  # "admin" or "device"
    expires_in_days: Optional[int] = None


async def create_key(self, request: Request, body: CreateKeyRequest):
    """
    Create a new API key. Returns the raw key ONCE (not stored).
    """
    if body.role not in ("admin", "device"):
        raise HTTPException(status_code=400, detail="Role must be 'admin' or 'device'")

    # Generate secure random key
    raw_key = f"gsk_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    doc = {
        "name": body.name,
        "role": body.role,
        "key_hash": key_hash,
        "key_prefix": raw_key[:8],
        "is_active": True,
        "created_at": datetime.now(),
        "last_used_at": None,
        "expires_at": None,
    }

    if body.expires_in_days:
        from datetime import timedelta
        doc["expires_at"] = datetime.now() + timedelta(days=body.expires_in_days)

    db = self._get_db()
    db["api_keys"].insert_one(doc)

    return {
        "status": True,
        "message": "API key created. Save this key - it won't be shown again.",
        "data": {
            "key": raw_key,
            "name": body.name,
            "role": body.role,
            "expires_at": doc["expires_at"].isoformat() if doc["expires_at"] else None,
        }
    }

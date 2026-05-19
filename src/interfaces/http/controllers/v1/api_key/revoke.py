"""
Revoke API Key endpoint.
"""

from datetime import datetime

from bson import ObjectId
from fastapi import HTTPException, Request


async def revoke_key(self, request: Request, key_id: str):
    """Revoke (deactivate) an API key."""
    db = self._get_db()

    try:
        obj_id = ObjectId(key_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid key ID")

    result = db["api_keys"].update_one(
        {"_id": obj_id},
        {"$set": {"is_active": False, "revoked_at": datetime.now()}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="API key not found")

    return {"status": True, "message": "API key revoked"}

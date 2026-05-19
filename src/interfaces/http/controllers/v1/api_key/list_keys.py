"""
List API Keys endpoint.
"""

from fastapi import Request


async def list_keys(self, request: Request):
    """List all API keys (without showing the actual key)."""
    db = self._get_db()
    keys = list(db["api_keys"].find(
        {},
        {"key_hash": 0}  # Never expose hash
    ).sort("created_at", -1))

    data = []
    for k in keys:
        data.append({
            "id": str(k["_id"]),
            "name": k.get("name"),
            "role": k.get("role"),
            "key_prefix": k.get("key_prefix", "***"),
            "is_active": k.get("is_active"),
            "created_at": k.get("created_at"),
            "last_used_at": k.get("last_used_at"),
            "expires_at": k.get("expires_at"),
        })

    return {"status": True, "data": data}

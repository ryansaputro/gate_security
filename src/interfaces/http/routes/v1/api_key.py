"""
API Key management routes (admin only).
"""

from fastapi import APIRouter, Depends
from interfaces.http.controllers.v1.api_key.interface import controller
from interfaces.http.middlewares.auth import require_auth

router = APIRouter(prefix="/api-keys", tags=["API Keys"])

# All API key management requires admin role
_admin_auth = Depends(require_auth(["admin"]))

router.post("", dependencies=[_admin_auth])(controller.create_key)
router.get("", dependencies=[_admin_auth])(controller.list_keys)
router.delete("/{key_id}", dependencies=[_admin_auth])(controller.revoke_key)

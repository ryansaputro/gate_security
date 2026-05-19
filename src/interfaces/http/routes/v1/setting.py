"""
Setting routes.
"""

from fastapi import APIRouter, Depends
from interfaces.http.controllers.v1.setting.interface import controller
from interfaces.http.middlewares.auth import require_auth

router = APIRouter(prefix="/settings", tags=["Settings"])

_admin_auth = Depends(require_auth(["admin"]))
_device_auth = Depends(require_auth(["admin", "device"]))

# Devices can read settings (needed for vote_threshold, confidence, etc)
router.get("", dependencies=[_admin_auth])(controller.list_settings)
router.get("/{key}", dependencies=[_device_auth])(controller.get_setting)
# Only admin can modify settings
router.post("", dependencies=[_admin_auth])(controller.upsert_setting)

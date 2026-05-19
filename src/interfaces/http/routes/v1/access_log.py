"""
Access Log routes.
"""

from fastapi import APIRouter, Depends
from interfaces.http.controllers.v1.access_log.interface import controller
from interfaces.http.middlewares.auth import require_auth

router = APIRouter(prefix="/access-logs", tags=["Access Logs"])

_admin_auth = Depends(require_auth(["admin"]))

router.get("", dependencies=[_admin_auth])(controller.list_recent)
router.get("/plate/{plate}", dependencies=[_admin_auth])(controller.by_plate)

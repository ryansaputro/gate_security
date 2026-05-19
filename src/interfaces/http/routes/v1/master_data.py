"""
Master Data routes.
"""

from fastapi import APIRouter, Depends
from interfaces.http.controllers.v1.master_data.interface import controller
from interfaces.http.middlewares.auth import require_auth

router = APIRouter(prefix="/master-data", tags=["Master Data"])

_admin_auth = Depends(require_auth(["admin"]))

router.get("/{type}", dependencies=[_admin_auth])(controller.list_by_type)
router.post("", dependencies=[_admin_auth])(controller.create_master_data)
router.delete("/{master_id}", dependencies=[_admin_auth])(controller.delete_master_data)

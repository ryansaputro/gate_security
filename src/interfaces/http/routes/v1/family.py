"""
Family routes.
"""

from fastapi import APIRouter, Depends
from interfaces.http.controllers.v1.family.interface import controller
from interfaces.http.middlewares.auth import require_auth

router = APIRouter(prefix="/families", tags=["Families"])

_admin_auth = Depends(require_auth(["admin"]))

router.get("", dependencies=[_admin_auth])(controller.list_families)
router.get("/{family_id}", dependencies=[_admin_auth])(controller.get_family)
router.post("", dependencies=[_admin_auth])(controller.create_family)
router.put("/{family_id}", dependencies=[_admin_auth])(controller.update_family)
router.delete("/{family_id}", dependencies=[_admin_auth])(controller.delete_family)

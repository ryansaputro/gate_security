"""
House routes.
"""

from fastapi import APIRouter, Depends
from interfaces.http.controllers.v1.house.interface import controller
from interfaces.http.middlewares.auth import require_auth

router = APIRouter(prefix="/houses", tags=["Houses"])

_admin_auth = Depends(require_auth(["admin"]))

router.get("", dependencies=[_admin_auth])(controller.list_houses)
router.get("/{house_id}", dependencies=[_admin_auth])(controller.get_house)
router.post("", dependencies=[_admin_auth])(controller.create_house)
router.put("/{house_id}", dependencies=[_admin_auth])(controller.update_house)
router.delete("/{house_id}", dependencies=[_admin_auth])(controller.delete_house)

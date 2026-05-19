"""
Due (Iuran) routes.
"""

from fastapi import APIRouter, Depends
from interfaces.http.controllers.v1.due.interface import controller
from interfaces.http.middlewares.auth import require_auth

router = APIRouter(prefix="/dues", tags=["Dues (Iuran)"])

_admin_auth = Depends(require_auth(["admin"]))

router.get("/family/{family_id}", dependencies=[_admin_auth])(controller.list_unpaid)
router.post("", dependencies=[_admin_auth])(controller.create_due)
router.post("/pay", dependencies=[_admin_auth])(controller.pay_due)

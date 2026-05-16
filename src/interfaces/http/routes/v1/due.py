"""
Due (Iuran) routes.
"""

from fastapi import APIRouter
from interfaces.http.controllers.v1.due.interface import controller

router = APIRouter(prefix="/dues", tags=["Dues (Iuran)"])

router.get("/family/{family_id}")(controller.list_unpaid)
router.post("")(controller.create_due)
router.post("/pay")(controller.pay_due)

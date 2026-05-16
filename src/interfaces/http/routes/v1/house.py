"""
House routes.
"""

from fastapi import APIRouter
from interfaces.http.controllers.v1.house.interface import controller

router = APIRouter(prefix="/houses", tags=["Houses"])

router.get("")(controller.list_houses)
router.get("/{house_id}")(controller.get_house)
router.post("")(controller.create_house)
router.put("/{house_id}")(controller.update_house)
router.delete("/{house_id}")(controller.delete_house)

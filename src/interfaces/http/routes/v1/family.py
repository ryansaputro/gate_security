"""
Family routes.
"""

from fastapi import APIRouter
from interfaces.http.controllers.v1.family.interface import controller

router = APIRouter(prefix="/families", tags=["Families"])

router.get("")(controller.list_families)
router.get("/{family_id}")(controller.get_family)
router.post("")(controller.create_family)
router.put("/{family_id}")(controller.update_family)
router.delete("/{family_id}")(controller.delete_family)

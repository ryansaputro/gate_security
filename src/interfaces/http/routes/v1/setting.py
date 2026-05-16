"""
Setting routes.
"""

from fastapi import APIRouter
from interfaces.http.controllers.v1.setting.interface import controller

router = APIRouter(prefix="/settings", tags=["Settings"])

router.get("")(controller.list_settings)
router.get("/{key}")(controller.get_setting)
router.post("")(controller.upsert_setting)

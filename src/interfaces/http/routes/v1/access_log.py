"""
Access Log routes.
"""

from fastapi import APIRouter
from interfaces.http.controllers.v1.access_log.interface import controller

router = APIRouter(prefix="/access-logs", tags=["Access Logs"])

router.get("")(controller.list_recent)
router.get("/plate/{plate}")(controller.by_plate)

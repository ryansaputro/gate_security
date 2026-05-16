"""
Master Data routes.
"""

from fastapi import APIRouter
from interfaces.http.controllers.v1.master_data.interface import controller

router = APIRouter(prefix="/master-data", tags=["Master Data"])

router.get("/{type}")(controller.list_by_type)
router.post("")(controller.create_master_data)
router.delete("/{master_id}")(controller.delete_master_data)

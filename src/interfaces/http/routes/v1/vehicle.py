"""
Vehicle routes.
"""

from fastapi import APIRouter
from interfaces.http.controllers.v1.vehicle.interface import controller

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])

router.get("")(controller.list_vehicles)
router.get("/plate/{plate}")(controller.get_by_plate)
router.get("/{vehicle_id}")(controller.get_vehicle)
router.post("")(controller.create_vehicle)

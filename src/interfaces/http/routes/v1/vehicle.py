"""
Vehicle routes.
"""

from fastapi import APIRouter, Depends
from interfaces.http.controllers.v1.vehicle.interface import controller
from interfaces.http.middlewares.auth import require_auth

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])

_admin_auth = Depends(require_auth(["admin"]))

router.get("", dependencies=[_admin_auth])(controller.list_vehicles)
router.get("/plate/{plate}", dependencies=[_admin_auth])(controller.get_by_plate)
router.get("/{vehicle_id}", dependencies=[_admin_auth])(controller.get_vehicle)
router.post("", dependencies=[_admin_auth])(controller.create_vehicle)

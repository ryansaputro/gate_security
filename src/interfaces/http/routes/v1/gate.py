"""
Gate routes (mirrors basecode-golang routes/v1/user.go pattern).
"""

from fastapi import APIRouter
from interfaces.http.controllers.v1.gate.interface import controller

router = APIRouter(prefix="/gate", tags=["Gate Validation"])

router.post("/validate-rfid")(controller.validate_rfid)
router.post("/validate-plate")(controller.validate_plate)

"""
Gate routes (mirrors basecode-golang routes/v1/user.go pattern).
"""

from fastapi import APIRouter, Depends
from interfaces.http.controllers.v1.gate.interface import controller
from interfaces.http.middlewares.auth import require_auth

router = APIRouter(prefix="/gate", tags=["Gate Validation"])

# Gate validation: accessible by both device and admin
_gate_auth = Depends(require_auth(["admin", "device"]))

router.post("/validate-rfid", dependencies=[_gate_auth])(controller.validate_rfid)
router.post("/validate-plate", dependencies=[_gate_auth])(controller.validate_plate)

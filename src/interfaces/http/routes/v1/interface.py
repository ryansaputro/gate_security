"""
V1 Routes Interface (mirrors basecode-golang interfaces/http/routes/v1/interface.go).
Mounts all v1 route groups.
"""

from fastapi import FastAPI

from interfaces.http.routes.v1.gate import router as gate_router
from interfaces.http.routes.v1.house import router as house_router
from interfaces.http.routes.v1.vehicle import router as vehicle_router
from interfaces.http.routes.v1.guest import router as guest_router
from interfaces.http.routes.v1.access_log import router as access_log_router
from interfaces.http.routes.v1.due import router as due_router
from interfaces.http.routes.v1.family import router as family_router
from interfaces.http.routes.v1.rfid_card import router as rfid_card_router
from interfaces.http.routes.v1.event import router as event_router
from interfaces.http.routes.v1.setting import router as setting_router
from interfaces.http.routes.v1.master_data import router as master_data_router


def mount_v1_routes(app: FastAPI, prefix: str = "/v1"):
    """Mount all v1 routes (mirrors MountXxx pattern)."""
    app.include_router(gate_router, prefix=prefix)
    app.include_router(house_router, prefix=prefix)
    app.include_router(vehicle_router, prefix=prefix)
    app.include_router(family_router, prefix=prefix)
    app.include_router(guest_router, prefix=prefix)
    app.include_router(rfid_card_router, prefix=prefix)
    app.include_router(access_log_router, prefix=prefix)
    app.include_router(due_router, prefix=prefix)
    app.include_router(event_router, prefix=prefix)
    app.include_router(setting_router, prefix=prefix)
    app.include_router(master_data_router, prefix=prefix)

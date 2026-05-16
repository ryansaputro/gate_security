"""
HTTP Launch (mirrors basecode-golang interfaces/http/launch.go).
Starts FastAPI server with all routes mounted.

Run: uvicorn interfaces.http.launch:app --reload --port 3000
Swagger: http://localhost:3000/docs
ReDoc:   http://localhost:3000/redoc
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from interfaces.http.routes.v1.interface import mount_v1_routes

app = FastAPI(
    title="Gate Security Service API",
    description=(
        "REST API for Residential Gate Security System.\n\n"
        "- Gate validation (RFID + Plate OCR)\n"
        "- House & Family management\n"
        "- Vehicle registration\n"
        "- Guest management\n"
        "- Access logging\n"
        "- Dues (Iuran) tracking"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
base_path = os.getenv("BASE_PATH", "")
mount_v1_routes(app, prefix=f"{base_path}/v1")

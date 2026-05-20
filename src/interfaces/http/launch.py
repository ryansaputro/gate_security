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

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from interfaces.http.routes.v1.interface import mount_v1_routes
from interfaces.web.routes import router as web_router
from interfaces.web.live_monitor import router as live_monitor_router

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

# Mount web admin panel
app.include_router(web_router)
app.include_router(live_monitor_router)


# Global error handler — catch DB errors and show friendly message
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = str(exc)

    # Parse pymongo DuplicateKeyError into friendly message
    if "DuplicateKeyError" in type(exc).__name__ or "E11000" in error_msg:
        # Extract dup key info
        import re as _re
        match = _re.search(r'dup key: \{(.+?)\}', error_msg)
        friendly = f"Data sudah ada (duplicate): {match.group(1)}" if match else "Data sudah ada (duplicate key)"
    elif "InvalidId" in type(exc).__name__:
        friendly = "ID tidak valid"
    else:
        friendly = f"Error: {error_msg[:200]}"

    # If request is for admin panel (web), redirect back with error
    if request.url.path.startswith("/admin"):
        referer = request.headers.get("referer", "/admin/")
        # Return a simple error page
        html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Error</title>
        <script src="https://cdn.tailwindcss.com"></script></head>
        <body class="bg-gray-100 min-h-screen flex items-center justify-center">
        <div class="bg-white rounded-lg shadow-lg p-8 max-w-lg">
        <h2 class="text-xl font-bold text-red-600 mb-4">⚠️ Error</h2>
        <p class="text-gray-700 mb-4">{friendly}</p>
        <a href="{referer}" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">← Kembali</a>
        </div></body></html>"""
        return HTMLResponse(content=html, status_code=400)

    # For API requests, return JSON
    return JSONResponse(status_code=400, content={"status": False, "message": friendly})

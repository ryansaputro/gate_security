"""
Live Monitor Routes - Reads from shared_state (produced by live_paddle_ocr.py).

The CMD process (make local-cmd-v3) is the producer.
This web route is the consumer — it reads frames + detections from shared state.

Provides:
- /admin/live-monitor         → Live monitor page
- /admin/live-monitor/stream  → MJPEG stream (reads frames from shared_state)
- /admin/live-monitor/events  → SSE realtime plate detection log
- /admin/live-monitor/gate-open → Manual gate open trigger
- /admin/live-monitor/status  → OCR process status (JSON)
"""

import asyncio
import os
import time
import json
from datetime import datetime
from typing import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, JSONResponse

router = APIRouter(prefix="/admin/live-monitor", tags=["live-monitor"])


# --- MJPEG Stream (reads from shared_state) ---

def _generate_mjpeg():
    """Generator that yields MJPEG frames from shared_state."""
    import cv2
    import numpy as np
    from shared_state import get_latest_frame, get_status

    no_signal_frame = None
    last_frame_bytes = None

    while True:
        frame_bytes, frame_time = get_latest_frame()

        if frame_bytes and (time.time() - frame_time) < 5:
            last_frame_bytes = frame_bytes
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
                   + frame_bytes + b'\r\n')
        else:
            # No fresh frame — show "waiting for OCR process" placeholder
            if no_signal_frame is None:
                img = np.zeros((480, 640, 3), dtype=np.uint8)
                # Dark background with message
                cv2.putText(img, "Waiting for OCR process...", (100, 220),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (100, 100, 100), 2)
                cv2.putText(img, "Run: make local-cmd-v3", (150, 270),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (80, 80, 80), 1)
                status = get_status()
                if status.get("running"):
                    cv2.putText(img, "OCR running but no frames yet", (120, 320),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 1)
                _, buf = cv2.imencode('.jpg', img)
                no_signal_frame = buf.tobytes()

            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
                   + no_signal_frame + b'\r\n')

        # ~15 FPS when frames available, 1 FPS when waiting
        if frame_bytes:
            time.sleep(0.066)
        else:
            time.sleep(1.0)


# --- SSE Events (reads detections from shared_state) ---

async def _event_generator() -> AsyncGenerator[str, None]:
    """Async generator for SSE events from shared_state."""
    from shared_state import get_detections_since, get_status

    # Start from -1 to get ALL existing events on first connect
    last_seq = -1
    heartbeat_counter = 0

    while True:
        # Poll every 100ms for near-realtime response
        await asyncio.sleep(0.1)
        heartbeat_counter += 1

        # Check for new detections
        new_events = get_detections_since(last_seq)
        if new_events:
            for event in new_events:
                last_seq = event.get("seq", last_seq)
                yield f"data: {json.dumps(event)}\n\n"
            heartbeat_counter = 0
        elif heartbeat_counter >= 150:  # heartbeat every ~15s
            heartbeat_counter = 0
            status = get_status()
            yield f": heartbeat running={status.get('running', False)}\n\n"


# --- Routes ---

@router.get("", response_class=HTMLResponse)
def live_monitor_page(request: Request):
    """Render live monitor page."""
    from interfaces.web.routes import require_module, render
    user, err = require_module(request, "live_monitor")
    if err:
        return err
    return render("live_monitor.html", user=user, active="live_monitor")


@router.get("/stream")
def mjpeg_stream(request: Request):
    """MJPEG stream — proxies frames from the running OCR process."""
    from interfaces.web.routes import require_module
    user, err = require_module(request, "live_monitor")
    if err:
        return JSONResponse(status_code=401, content={"message": "Unauthorized"})
    return StreamingResponse(
        _generate_mjpeg(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/events")
async def sse_events(request: Request):
    """SSE endpoint — streams plate detection events from the OCR process."""
    from interfaces.web.routes import require_module
    user, err = require_module(request, "live_monitor")
    if err:
        return JSONResponse(status_code=401, content={"message": "Unauthorized"})
    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/status")
def ocr_status(request: Request):
    """Get OCR process status."""
    from interfaces.web.routes import require_module
    from shared_state import get_status, get_latest_frame
    user, err = require_module(request, "live_monitor")
    if err:
        return JSONResponse(status_code=401, content={"message": "Unauthorized"})

    status = get_status()
    _, frame_time = get_latest_frame()
    status["has_frame"] = frame_time > 0 and (time.time() - frame_time) < 5
    return JSONResponse(content=status)


@router.post("/gate-open")
def manual_gate_open(request: Request):
    """Manually trigger gate open."""
    from interfaces.web.routes import require_module
    user, err = require_module(request, "live_monitor")
    if err:
        return JSONResponse(status_code=401, content={"message": "Unauthorized"})

    try:
        from interfaces.cmd.gate_client import _trigger_gate_open
        _trigger_gate_open()

        # Log manual open
        from drivers.mongo.connection import Mongo
        db = Mongo().get_db()
        db.access_logs.insert_one({
            "gate_id": os.getenv("GATE_ID", "gate_1"),
            "direction": "entry",
            "method": "manual",
            "validation_result": "granted",
            "denied_reason": "",
            "plate_detected": "",
            "plate_confidence": 0,
            "is_resident": False,
            "timestamp": datetime.utcnow(),
            "opened_by": user.get("username", "admin"),
        })

        return JSONResponse(content={"status": True, "message": "Gate opened successfully"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": False, "message": f"Failed: {str(e)}"})

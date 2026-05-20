"""
Shared State - Bridge between live_paddle_ocr.py (CMD) and web Live Monitor.

The CMD process (local-cmd-v3) writes frames + detections here.
The web admin reads from here to display MJPEG stream + SSE events.

This uses threading primitives so both can run in the same process,
OR file-based IPC (shared /tmp files) when running as separate processes.
"""

import threading
import time
import json
import os
import cv2
import numpy as np
from datetime import datetime
from collections import deque

# --- In-process shared state (when running in same process) ---
_lock = threading.Lock()
_latest_frame: np.ndarray = None
_latest_frame_time: float = 0
_detections: deque = deque(maxlen=200)
_detection_seq: int = 0
_seq_initialized: bool = False

# --- IPC paths (when running as separate processes) ---
_IPC_DIR = os.getenv("OCR_IPC_DIR", "/tmp/ocr-live")
_IPC_FRAME_PATH = os.path.join(_IPC_DIR, "frame.jpg")
_IPC_DETECTIONS_PATH = os.path.join(_IPC_DIR, "detections.jsonl")
_IPC_STATUS_PATH = os.path.join(_IPC_DIR, "status.json")


def _ensure_ipc_dir():
    os.makedirs(_IPC_DIR, exist_ok=True)


# ==================== PRODUCER (called by live_paddle_ocr.py) ====================

def publish_frame(frame: np.ndarray):
    """Publish latest camera frame (called by OCR process)."""
    global _latest_frame, _latest_frame_time
    with _lock:
        _latest_frame = frame.copy()
        _latest_frame_time = time.time()

    # Also write to IPC file for cross-process access
    try:
        _ensure_ipc_dir()
        _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        # Atomic write via temp file
        tmp_path = _IPC_FRAME_PATH + ".tmp"
        with open(tmp_path, 'wb') as f:
            f.write(buf.tobytes())
        os.replace(tmp_path, _IPC_FRAME_PATH)
    except Exception:
        pass


def publish_detection(plate: str, confidence: float, votes: int,
                      granted: bool = None, reason: str = "",
                      bbox: tuple = None):
    """Publish a plate detection event (called by OCR process)."""
    global _detection_seq, _seq_initialized

    # Initialize seq from file on first call (cross-process resume)
    if not _seq_initialized:
        _seq_initialized = True
        try:
            if os.path.exists(_IPC_DETECTIONS_PATH):
                with open(_IPC_DETECTIONS_PATH, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                ev = json.loads(line)
                                _detection_seq = max(_detection_seq, ev.get("seq", 0) + 1)
                            except json.JSONDecodeError:
                                pass
        except Exception:
            pass

    event = {
        "seq": _detection_seq,
        "plate": plate,
        "confidence": confidence,
        "votes": votes,
        "granted": granted,
        "reason": reason,
        "bbox": list(bbox) if bbox else None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    with _lock:
        _detections.append(event)
        _detection_seq += 1

    # Append to IPC file immediately (flush for instant pickup)
    try:
        _ensure_ipc_dir()
        with open(_IPC_DETECTIONS_PATH, 'a') as f:
            f.write(json.dumps(event) + "\n")
            f.flush()
            os.fsync(f.fileno())
        # Trim file if too large (keep last 200 lines)
        _trim_detections_file()
    except Exception:
        pass


def publish_status(running: bool, device: str = "", model: str = "",
                   interval: float = 0, fps: float = 0):
    """Publish OCR process status."""
    status = {
        "running": running,
        "device": device,
        "model": model,
        "interval": interval,
        "fps": fps,
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }
    try:
        _ensure_ipc_dir()
        tmp_path = _IPC_STATUS_PATH + ".tmp"
        with open(tmp_path, 'w') as f:
            json.dump(status, f)
        os.replace(tmp_path, _IPC_STATUS_PATH)
    except Exception:
        pass


# ==================== CONSUMER (called by web Live Monitor) ====================

def get_latest_frame() -> tuple:
    """Get latest frame. Returns (frame_bytes_jpg, timestamp) or (None, 0)."""
    # Try in-process first
    with _lock:
        if _latest_frame is not None and (time.time() - _latest_frame_time) < 5:
            _, buf = cv2.imencode('.jpg', _latest_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            return buf.tobytes(), _latest_frame_time

    # Fallback: read from IPC file
    try:
        if os.path.exists(_IPC_FRAME_PATH):
            mtime = os.path.getmtime(_IPC_FRAME_PATH)
            if (time.time() - mtime) < 5:  # frame is fresh (< 5s old)
                with open(_IPC_FRAME_PATH, 'rb') as f:
                    return f.read(), mtime
    except Exception:
        pass

    return None, 0


def get_detections_since(seq: int) -> list:
    """Get all detections since sequence number. Returns list of event dicts."""
    # Try in-process first (instant, no I/O)
    with _lock:
        results = [d for d in _detections if d["seq"] > seq]
        if results:
            return results

    # Fallback: read from IPC file (cross-process)
    try:
        if not os.path.exists(_IPC_DETECTIONS_PATH):
            return []

        # Quick mtime check — only skip if file unchanged AND we already read with this seq
        mtime = os.path.getmtime(_IPC_DETECTIONS_PATH)
        cache = getattr(get_detections_since, '_cache', {'mtime': 0, 'seq': -2})
        if mtime == cache['mtime'] and seq == cache['seq']:
            return []

        results = []
        with open(_IPC_DETECTIONS_PATH, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    if event.get("seq", 0) > seq:
                        results.append(event)
                except json.JSONDecodeError:
                    continue

        # Update cache only if no results (so next poll with same seq skips)
        if not results:
            get_detections_since._cache = {'mtime': mtime, 'seq': seq}

        return results
    except Exception:
        pass

    return []


def get_status() -> dict:
    """Get OCR process status."""
    try:
        if os.path.exists(_IPC_STATUS_PATH):
            with open(_IPC_STATUS_PATH, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {"running": False}


def get_latest_seq() -> int:
    """Get the latest detection sequence number."""
    with _lock:
        if _detections:
            return _detections[-1]["seq"]
    return _detection_seq


# ==================== HELPERS ====================

def _trim_detections_file():
    """Keep detections file to last 200 lines."""
    try:
        with open(_IPC_DETECTIONS_PATH, 'r') as f:
            lines = f.readlines()
        if len(lines) > 200:
            with open(_IPC_DETECTIONS_PATH, 'w') as f:
                f.writelines(lines[-200:])
    except Exception:
        pass

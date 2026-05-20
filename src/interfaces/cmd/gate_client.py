"""
Gate Client - Calls the HTTP API to validate plate and trigger gate open.
Used by the CMD interface (live OCR) after confident plate detection.
"""

import os
import requests
import time


API_BASE = os.getenv("GATE_API_URL", "http://localhost:3000")
API_KEY = os.getenv("GATE_API_KEY", "")
GATE_ID = os.getenv("GATE_ID", "gate_1")
DIRECTION = os.getenv("GATE_DIRECTION", "entry")
COOLDOWN_SECONDS = int(os.getenv("GATE_COOLDOWN", "10"))

_last_open_time = 0
_last_plate = ""
_vote_threshold = None


def _get_vote_threshold() -> int:
    """Get vote_threshold from settings collection (cached per session)."""
    global _vote_threshold
    if _vote_threshold is not None:
        return _vote_threshold
    try:
        headers = {}
        if API_KEY:
            headers["X-API-Key"] = API_KEY
        resp = requests.get(f"{API_BASE}/v1/settings/ocr_vote_threshold",
                            headers=headers, timeout=3)
        data = resp.json()
        val = data.get("data", {}).get("value", "3")
        _vote_threshold = int(val) if val else 3
    except Exception:
        _vote_threshold = 3
    return _vote_threshold


def validate_and_open(plate: str, confidence: float, votes: int):
    """
    Called by live_easyocr when plate is detected with enough votes.
    Hits API → if granted → trigger gate open.
    """
    global _last_open_time, _last_plate

    # Don't spam: cooldown per plate
    now = time.time()
    if plate == _last_plate and (now - _last_open_time) < COOLDOWN_SECONDS:
        return None

    vote_threshold = _get_vote_threshold()
    if votes < vote_threshold:
        return None

    try:
        headers = {}
        if API_KEY:
            headers["X-API-Key"] = API_KEY

        resp = requests.post(
            f"{API_BASE}/v1/gate/validate-plate",
            json={
                "plate_detected": plate,
                "confidence": confidence,
                "gate_id": GATE_ID,
                "direction": DIRECTION,
            },
            headers=headers,
            timeout=5,
        )
        data = resp.json()

        if data.get("status") and data.get("data", {}).get("granted"):
            print(f"  ✅ GATE OPEN - {plate} (granted)")
            _trigger_gate_open()
            _last_open_time = time.time()
            _last_plate = plate
            return ("granted", "Gate opened")
        else:
            reason = data.get("data", {}).get("reason") or data.get("message", "denied")
            print(f"  ❌ DENIED - {plate}: {reason}")
            return ("denied", reason)

    except requests.exceptions.ConnectionError:
        print(f"  ⚠️  API not reachable ({API_BASE})")
        return ("error", f"API not reachable ({API_BASE})")
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
        return ("error", str(e))


def _trigger_gate_open():
    """
    Trigger physical gate open.
    Options (configure via GATE_OPEN_METHOD env):
    - "gpio": Raspberry Pi GPIO relay
    - "http": HTTP call to gate controller
    - "log": Just log (for testing)
    """
    method = os.getenv("GATE_OPEN_METHOD", "log")

    if method == "gpio":
        _open_gpio()
    elif method == "http":
        _open_http()
    else:
        # Default: just log
        print("  🚧 Gate trigger: LOG mode (set GATE_OPEN_METHOD=gpio|http)")


def _open_gpio():
    """Open gate via Raspberry Pi GPIO relay."""
    try:
        import RPi.GPIO as GPIO
        pin = int(os.getenv("GATE_GPIO_PIN", "17"))
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(float(os.getenv("GATE_OPEN_DURATION", "3")))
        GPIO.output(pin, GPIO.LOW)
        GPIO.cleanup(pin)
        print(f"  🔓 GPIO pin {pin} triggered")
    except ImportError:
        print("  ⚠️  RPi.GPIO not available (not on Raspberry Pi?)")
    except Exception as e:
        print(f"  ⚠️  GPIO error: {e}")


def _open_http():
    """Open gate via HTTP call to gate controller hardware."""
    url = os.getenv("GATE_OPEN_URL", "http://192.168.1.100/open")
    try:
        requests.get(url, timeout=3)
        print(f"  🔓 HTTP gate trigger sent to {url}")
    except Exception as e:
        print(f"  ⚠️  HTTP gate error: {e}")

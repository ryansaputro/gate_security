#!/usr/bin/env python3
"""
Indonesian Plate Detection v3 - YOLO + PaddleOCR Pipeline

Faster than EasyOCR (~0.2s vs ~0.9s per frame).

Usage:
  python3 src/live_paddle_ocr.py
  python3 src/live_paddle_ocr.py --model models/plate_best.pt
  python3 src/live_paddle_ocr.py --model models/plate_best.pt --device "rtsp://..."
"""

import cv2
import numpy as np
import argparse
import time
import re
import threading
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plate_format import format_plate


class FrameGrabber:
    """Threaded frame grabber for RTSP/HTTP streams."""
    def __init__(self, source):
        self.cap = cv2.VideoCapture(source)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.ret = False
        self.frame = None
        self.running = True
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._grab, daemon=True)
        self.thread.start()

    def _grab(self):
        while self.running:
            ret, frame = self.cap.read()
            with self.lock:
                self.ret = ret
                self.frame = frame

    def read(self):
        with self.lock:
            if self.frame is not None:
                return self.ret, self.frame.copy()
            return False, None

    def release(self):
        self.running = False
        self.cap.release()


class PlateDetectorPaddle:
    """YOLO plate detection + PaddleOCR text reading."""

    def __init__(self, model_path=None, conf_threshold=0.4):
        from ultralytics import YOLO
        from paddleocr import PaddleOCR

        if model_path and os.path.exists(model_path):
            print(f"Loading custom YOLO model: {model_path}")
            self.model = YOLO(model_path)
        else:
            print("Loading YOLOv8n (generic)...")
            self.model = YOLO("yolov8n.pt")

        self.conf_threshold = conf_threshold
        self.ocr = PaddleOCR(lang="en", show_log=False)

    def detect(self, frame):
        """Detect plates using YOLO, then read text with PaddleOCR."""
        results = self.model(frame, verbose=False, conf=self.conf_threshold)
        detections = []

        plate_boxes = []
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                plate_boxes.append((x1, y1, x2, y2))

        if not plate_boxes:
            return detections

        # Preprocess full frame for OCR
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        processed = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

        # Run PaddleOCR
        ocr_results = self.ocr.ocr(processed, cls=False)

        if not ocr_results or not ocr_results[0]:
            return detections

        # Filter plate candidates
        for line in ocr_results[0]:
            bbox, (text, conf) = line[0], line[1]
            if conf < 0.3:
                continue
            clean = re.sub(r'[^A-Z0-9]', '', text.upper())
            if len(clean) < 4 or len(clean) > 12:
                continue
            has_letter = any(c.isalpha() for c in clean)
            has_digit = any(c.isdigit() for c in clean)
            if not (has_letter and has_digit):
                continue
            if not any(c.isalpha() for c in clean[:2]):
                continue

            formatted = format_plate(clean)
            result = formatted if formatted else clean
            detections.append((result, conf, plate_boxes[0]))

        return detections


def main():
    parser = argparse.ArgumentParser(description="Plate Detection v3 (YOLO+PaddleOCR)")
    parser.add_argument("--device", default="0", help="Camera ID or stream URL")
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--model", default=None, help="Path to YOLO .pt model")
    parser.add_argument("--conf", type=float, default=0.4)
    parser.add_argument("--image", default=None, help="Test on single image")
    parser.add_argument("--gui", action="store_true", help="Show GUI window (requires GTK)")
    args = parser.parse_args()

    use_gui = False
    if args.gui:
        try:
            test_img = np.zeros((1, 1, 3), dtype=np.uint8)
            cv2.imshow("_test", test_img)
            cv2.destroyWindow("_test")
            cv2.waitKey(1)
            use_gui = True
        except cv2.error:
            print("  [WARN] --gui requested but OpenCV has no GTK support, running headless")

    # Image mode
    if args.image:
        print(f"Testing on image: {args.image}")
        detector = PlateDetectorPaddle(model_path=args.model, conf_threshold=args.conf)
        frame = cv2.imread(args.image)
        if frame is None:
            print(f"Cannot read image: {args.image}")
            return

        t = time.time()
        detections = detector.detect(frame)
        elapsed = time.time() - t
        print(f"  Detection time: {elapsed:.2f}s")

        if not detections:
            print("  No plates detected.")
        for (text, conf, (x1, y1, x2, y2)) in detections:
            print(f"  [{conf:.0%}] {text} | box=({x1},{y1},{x2},{y2})")
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        cv2.imwrite("/tmp/plate-v3-result.png", frame)
        print(f"  Result saved to /tmp/plate-v3-result.png")
        return

    # Live camera mode
    source = int(args.device) if args.device.isdigit() else args.device
    is_stream = isinstance(source, str)

    print("=" * 50)
    print("  Plate Detection v3 - YOLO + PaddleOCR")
    print("=" * 50)

    detector = PlateDetectorPaddle(model_path=args.model, conf_threshold=args.conf)

    if is_stream:
        grabber = FrameGrabber(source)
        time.sleep(3)
        ret, _ = grabber.read()
        if not ret:
            print("Cannot connect to stream")
            grabber.release()
            return
    else:
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            print(f"Cannot open camera {source}")
            return
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    # Publish status to shared state (for web Live Monitor)
    try:
        from shared_state import publish_frame, publish_detection, publish_status
        publish_status(True, device=str(source), model=args.model or "", interval=args.interval)
        _has_shared_state = True
        print("  [shared_state] Connected — web Live Monitor will receive data")
    except ImportError as e:
        _has_shared_state = False
        print(f"  [shared_state] Not available ({e}) — web Live Monitor disabled")

    print(f"Interval: {args.interval}s | Mode: {'GUI' if use_gui else 'headless'} | Ctrl+C to quit")
    last_detect = 0
    plate_text, plate_confidence = "", 0.0
    best_plates = {}

    try:
        while True:
            ret, frame = (grabber.read() if is_stream else cap.read())
            if not ret or frame is None:
                time.sleep(0.05)
                continue

            now = time.time()

            # Publish frame to shared state (for web MJPEG stream)
            if _has_shared_state:
                publish_frame(frame)

            if now - last_detect >= args.interval:
                last_detect = now
                t_start = time.time()
                for (text, conf, (x1, y1, x2, y2)) in detector.detect(frame):
                    best_plates[text] = best_plates.get(text, 0) + 1
                    if conf > plate_confidence or best_plates.get(text, 0) >= 2:
                        plate_text, plate_confidence = text, conf
                        dt = time.time() - t_start
                        print(f"  [{conf:.0%}] {text} (votes: {best_plates[text]}) [{dt:.2f}s]")

                        # Always publish detection to shared state (same as CMD log)
                        if _has_shared_state:
                            publish_detection(
                                plate=text, confidence=conf,
                                votes=best_plates[text],
                                granted=None, reason=f"{dt:.2f}s",
                                bbox=(x1, y1, x2, y2),
                            )

                        # Gate validation (separate from detection publishing)
                        try:
                            from interfaces.cmd.gate_client import validate_and_open
                            result = validate_and_open(plate_text, plate_confidence, best_plates[text])
                            if result is not None and _has_shared_state:
                                if isinstance(result, tuple) and len(result) == 2:
                                    status, reason = result
                                else:
                                    # Backward compat: old string return
                                    status = str(result)
                                    reason = str(result)
                                print(f"  [web→] {status}: {reason}")
                                publish_detection(
                                    plate=text, confidence=conf,
                                    votes=best_plates[text],
                                    granted=(status == "granted"),
                                    reason=reason,
                                    bbox=(x1, y1, x2, y2),
                                )
                        except Exception as e:
                            print(f"  [gate_client error] {e}")

                if len(best_plates) > 10:
                    best_plates = dict(sorted(best_plates.items(), key=lambda x: x[1], reverse=True)[:5])

            if use_gui:
                display = frame.copy()
                if plate_text:
                    cv2.rectangle(display, (5, 5), (500, 55), (0, 0, 0), -1)
                    cv2.putText(display, f"{plate_text} ({plate_confidence:.0%})",
                                (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 0), 2)
                cv2.imshow("Plate v3 (YOLO+PaddleOCR)", display)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q") or key == 27:
                    break
                elif key == ord("s"):
                    cv2.imwrite(f"/tmp/plate-v3-{int(now)}.png", frame)
                    print("  Saved!")
                elif key == ord("r"):
                    plate_text, plate_confidence, best_plates = "", 0.0, {}
                    print("  Reset!")
            else:
                time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n  Stopped.")

    if _has_shared_state:
        publish_status(False)

    (grabber.release() if is_stream else cap.release())
    if use_gui:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

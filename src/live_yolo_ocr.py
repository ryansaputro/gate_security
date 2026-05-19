#!/usr/bin/env python3
"""
Indonesian Plate Detection v2 - YOLO + EasyOCR Pipeline

Stage 1: YOLOv8n detects plate bounding box (fast, ~50-100ms)
Stage 2: EasyOCR reads text from cropped plate region only (accurate, ~100-200ms)

Much faster and more accurate than full-frame OCR.

Usage:
  python3 src/live_yolo_ocr.py
  python3 src/live_yolo_ocr.py --device "http://192.168.100.38:8080/video"
  python3 src/live_yolo_ocr.py --device "rtsp://user:pass@ip:554/live"
  python3 src/live_yolo_ocr.py --model path/to/custom_plate.pt

Model:
  Default uses a pre-trained license plate detection model.
  For best results, fine-tune YOLOv8n on your own gate camera images.
  See: docs/training-yolo-plate.md
"""

import cv2
import easyocr
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


class PlateDetectorYOLO:
    """YOLOv8n plate detection + EasyOCR text reading."""

    def __init__(self, model_path: str = None, conf_threshold: float = 0.4):
        from ultralytics import YOLO

        if model_path and os.path.exists(model_path):
            print(f"Loading custom YOLO model: {model_path}")
            self.model = YOLO(model_path)
        else:
            # Use pre-trained YOLOv8n — will detect "car", "truck", etc.
            # For plate-specific detection, provide a fine-tuned model.
            # Fallback: use generic yolov8n and detect plates via contour in ROI
            print("Loading YOLOv8n (generic)...")
            print("  Tip: For better accuracy, provide --model with a plate-trained .pt file")
            self.model = YOLO("yolov8n.pt")

        self.conf_threshold = conf_threshold
        self.reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        # Plate class IDs (if using custom model, class 0 = plate)
        # If using generic yolov8n: class 2=car, 3=motorcycle, 5=bus, 7=truck
        self.vehicle_classes = [2, 3, 5, 7]
        self.is_plate_model = model_path and os.path.exists(model_path)

    def detect(self, frame) -> list:
        """
        Detect plates in frame.
        Returns list of: (plate_text, confidence, bbox_xyxy)
        """
        results = self.model(frame, verbose=False, conf=self.conf_threshold)
        detections = []

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for box in boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                if self.is_plate_model:
                    # Custom plate model: box IS the plate
                    plate_crop = self._crop_plate(frame, x1, y1, x2, y2)
                    text, ocr_conf = self._read_plate_text(plate_crop)
                    if text:
                        detections.append((text, ocr_conf, (x1, y1, x2, y2)))
                else:
                    # Generic YOLO: box is vehicle, find plate within
                    if cls_id not in self.vehicle_classes:
                        continue
                    plate_region = self._find_plate_in_vehicle(frame, x1, y1, x2, y2)
                    if plate_region is not None:
                        px1, py1, px2, py2 = plate_region
                        plate_crop = self._crop_plate(frame, px1, py1, px2, py2)
                        text, ocr_conf = self._read_plate_text(plate_crop)
                        if text:
                            detections.append((text, ocr_conf, (px1, py1, px2, py2)))

        return detections

    def _crop_plate(self, frame, x1, y1, x2, y2, padding=5):
        """Crop plate region with padding."""
        h, w = frame.shape[:2]
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(w, x2 + padding)
        y2 = min(h, y2 + padding)
        return frame[y1:y2, x1:x2]

    def _find_plate_in_vehicle(self, frame, vx1, vy1, vx2, vy2):
        """Find plate rectangle within vehicle bounding box using contours."""
        # Focus on lower half of vehicle (plate is usually at bottom)
        mid_y = vy1 + (vy2 - vy1) // 3
        roi = frame[mid_y:vy2, vx1:vx2]

        if roi.size == 0:
            return None

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

        # Edge detection
        edges = cv2.Canny(gray, 50, 150)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        edges = cv2.dilate(edges, kernel, iterations=1)

        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        best_plate = None
        best_area = 0

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h
            if h == 0:
                continue
            ratio = w / h

            # Plate aspect ratio: ~2.5 to 5.0 for Indonesian plates
            if 2.0 <= ratio <= 6.0 and area > 800 and w > 60 and h > 15:
                if area > best_area:
                    best_area = area
                    best_plate = (vx1 + x, mid_y + y, vx1 + x + w, mid_y + y + h)

        return best_plate

    def _read_plate_text(self, plate_crop):
        """OCR on cropped plate image. Returns (formatted_text, confidence)."""
        if plate_crop is None or plate_crop.size == 0:
            return None, 0.0

        h, w = plate_crop.shape[:2]
        if w < 20 or h < 10:
            return None, 0.0

        # Preprocess: enhance contrast
        gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4))
        enhanced = clahe.apply(gray)

        # Resize for better OCR (EasyOCR works best with larger text)
        scale = max(1, 200 // w)
        if scale > 1:
            enhanced = cv2.resize(enhanced, (w * scale, h * scale),
                                  interpolation=cv2.INTER_CUBIC)

        enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

        # Run OCR
        results = self.reader.readtext(
            enhanced_bgr,
            paragraph=False,
            min_size=10,
            text_threshold=0.4,
            low_text=0.3,
        )

        if not results:
            return None, 0.0

        # Combine all detected text (plate might be split into parts)
        all_text = ""
        total_conf = 0.0
        count = 0

        for (_, text, conf) in results:
            if conf < 0.1:
                continue
            all_text += text
            total_conf += conf
            count += 1

        if not all_text or count == 0:
            return None, 0.0

        avg_conf = total_conf / count

        # Clean and format
        clean = re.sub(r"[^A-Z0-9]", "", all_text.upper())
        if len(clean) < 4:
            return None, 0.0

        formatted = format_plate(clean)
        result = formatted if formatted else clean

        # Basic validation: must have letters and digits
        has_letter = any(c.isalpha() for c in result.replace(" ", ""))
        has_digit = any(c.isdigit() for c in result.replace(" ", ""))
        if not (has_letter and has_digit):
            return None, 0.0

        return result, avg_conf


def main():
    parser = argparse.ArgumentParser(description="Plate Detection v2 (YOLO + OCR)")
    parser.add_argument("--device", default="0", help="Camera ID or stream URL")
    parser.add_argument("--interval", type=float, default=1.0, help="Detection interval (seconds)")
    parser.add_argument("--model", default=None, help="Path to YOLO plate model (.pt)")
    parser.add_argument("--conf", type=float, default=0.4, help="YOLO confidence threshold")
    args = parser.parse_args()

    source = int(args.device) if args.device.isdigit() else args.device
    is_stream = isinstance(source, str)

    print("=" * 50)
    print("  Plate Detection v2 - YOLO + EasyOCR")
    print("=" * 50)

    detector = PlateDetectorYOLO(model_path=args.model, conf_threshold=args.conf)

    if is_stream:
        grabber = FrameGrabber(source)
        print(f"Connecting to: {source}")
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

    print(f"Detection interval: {args.interval}s")
    print("Controls: q=quit, s=save, r=reset")
    print()

    last_detect = 0
    plate_text = ""
    plate_confidence = 0.0
    best_plates = {}  # voting: {plate: count}
    fps_counter = []

    while True:
        if is_stream:
            ret, frame = grabber.read()
        else:
            ret, frame = cap.read()

        if not ret or frame is None:
            time.sleep(0.05)
            continue

        now = time.time()
        display = frame.copy()

        if now - last_detect >= args.interval:
            t_start = time.time()
            last_detect = now

            detections = detector.detect(frame)
            t_elapsed = time.time() - t_start
            fps_counter.append(t_elapsed)
            if len(fps_counter) > 20:
                fps_counter.pop(0)

            for (text, conf, bbox) in detections:
                x1, y1, x2, y2 = bbox

                # Draw plate box
                cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(display, f"{text} ({conf:.0%})", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                # Voting
                best_plates[text] = best_plates.get(text, 0) + 1

                if conf > plate_confidence or best_plates.get(text, 0) >= 2:
                    plate_text = text
                    plate_confidence = conf
                    votes = best_plates[text]
                    print(f"  [{conf:.0%}] {text} (votes: {votes}, {t_elapsed*1000:.0f}ms)")

                    # Trigger gate validation
                    try:
                        from interfaces.cmd.gate_client import validate_and_open
                        validate_and_open(plate_text, plate_confidence, votes)
                    except Exception:
                        pass

            # Decay old votes
            if len(best_plates) > 10:
                best_plates = dict(
                    sorted(best_plates.items(), key=lambda x: x[1], reverse=True)[:5]
                )

        # HUD
        if plate_text:
            cv2.rectangle(display, (5, 5), (500, 55), (0, 0, 0), -1)
            cv2.putText(display, f"{plate_text} ({plate_confidence:.0%})",
                        (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 0), 2)

        # FPS
        if fps_counter:
            avg_ms = sum(fps_counter) / len(fps_counter) * 1000
            cv2.putText(display, f"{avg_ms:.0f}ms/detect", (10, display.shape[0] - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        cv2.imshow("Plate v2 (YOLO+OCR)", display)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:
            break
        elif key == ord("s"):
            cv2.imwrite(f"/tmp/plate-v2-{int(now)}.png", frame)
            print("  Saved!")
        elif key == ord("r"):
            plate_text = ""
            plate_confidence = 0.0
            best_plates = {}
            print("  Reset!")

    if is_stream:
        grabber.release()
    else:
        cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Indonesian Plate Detection v2 - YOLO + EasyOCR Pipeline

Stage 1: YOLOv8n detects plate bounding box (fast, ~50-100ms)
Stage 2: EasyOCR reads text from cropped plate region only (accurate, ~100-200ms)

Usage:
  python3 src/live_yolo_ocr.py
  python3 src/live_yolo_ocr.py --model models/plate_best.pt
  python3 src/live_yolo_ocr.py --model models/plate_best.pt --device "http://192.168.1.x:8080/video"
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

    def __init__(self, model_path=None, conf_threshold=0.4):
        from ultralytics import YOLO

        if model_path and os.path.exists(model_path):
            print(f"Loading custom YOLO model: {model_path}")
            self.model = YOLO(model_path)
            self.is_plate_model = True
        else:
            print("Loading YOLOv8n (generic)...")
            self.model = YOLO("yolov8n.pt")
            self.is_plate_model = False

        self.conf_threshold = conf_threshold
        self.reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        self.vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck

    def detect(self, frame):
        """
        Simple approach: YOLO checks if plate exists in frame.
        If yes, run full v1 OCR logic (no position filtering).
        YOLO box returned for display only.
        """
        results = self.model(frame, verbose=False, conf=self.conf_threshold)
        detections = []

        # Get plate boxes from YOLO
        plate_boxes = []
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                plate_boxes.append((x1, y1, x2, y2))

        if not plate_boxes:
            return detections

        # Plate detected! Run exact v1 OCR on full frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        processed = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

        ocr_results = self.reader.readtext(
            processed, paragraph=False, min_size=20,
            text_threshold=0.5, low_text=0.3,
        )

        if not ocr_results:
            return detections

        # Same plate candidate logic as v1
        for (bbox, text, conf) in ocr_results:
            if conf < 0.1:
                continue
            clean = re.sub(r'[^A-Z0-9]', '', text.upper())
            if len(clean) < 4 or len(clean) > 12:
                continue
            has_letter = any(c.isalpha() for c in clean)
            has_digit = any(c.isdigit() for c in clean)
            if not (has_letter and has_digit):
                continue
            # Check first 2 chars have a letter (area code)
            if not any(c.isalpha() for c in clean[:2]):
                continue

            formatted = format_plate(clean)
            result = formatted if formatted else clean

            # Use first YOLO box for display
            detections.append((result, conf, plate_boxes[0]))

        return detections

    def _crop(self, frame, x1, y1, x2, y2, pad=20):
        h, w = frame.shape[:2]
        return frame[max(0,y1-pad):min(h,y2+pad), max(0,x1-pad):min(w,x2+pad)]

    def _find_plate_contour(self, frame, vx1, vy1, vx2, vy2):
        mid_y = vy1 + (vy2 - vy1) // 3
        roi = frame[mid_y:vy2, vx1:vx2]
        if roi.size == 0:
            return None
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        gray = cv2.createCLAHE(2.0, (8,8)).apply(gray)
        edges = cv2.Canny(gray, 50, 150)
        edges = cv2.dilate(edges, np.ones((3,3), np.uint8), iterations=1)
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        best, best_area = None, 0
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if h == 0:
                continue
            ratio = w / h
            area = w * h
            if 2.0 <= ratio <= 6.0 and area > 800 and w > 60:
                if area > best_area:
                    best_area = area
                    best = (vx1+x, mid_y+y, vx1+x+w, mid_y+y+h)
        return best

    def _read_plate(self, crop):
        """Use same preprocessing approach as v1 (live_easyocr) which works."""
        if crop is None or crop.size == 0:
            return None, 0.0
        h, w = crop.shape[:2]
        if w < 20 or h < 10:
            return None, 0.0

        # Scale up significantly (v1 works on large frames)
        target_w = max(400, w * 3)
        scale = target_w / w
        crop_large = cv2.resize(crop, (int(w * scale), int(h * scale)),
                                interpolation=cv2.INTER_CUBIC)

        # Same preprocessing as v1 (preprocess_for_plate from live_easyocr)
        gray = cv2.cvtColor(crop_large, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        processed = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

        # Run EasyOCR same params as v1
        results = self.reader.readtext(
            processed,
            paragraph=False,
            min_size=20,
            text_threshold=0.5,
            low_text=0.3,
        )

        if not results:
            return None, 0.0

        # Combine all text (same as v1 merge approach)
        all_text, total_conf, count = "", 0.0, 0
        for (_, text, conf) in results:
            if conf < 0.1:
                continue
            all_text += text
            total_conf += conf
            count += 1

        if not all_text or count == 0:
            return None, 0.0

        clean = re.sub(r"[^A-Z0-9]", "", all_text.upper())
        if len(clean) < 4:
            return None, 0.0

        formatted = format_plate(clean)
        result = formatted if formatted else clean
        has_letter = any(c.isalpha() for c in result.replace(" ", ""))
        has_digit = any(c.isdigit() for c in result.replace(" ", ""))
        if not (has_letter and has_digit):
            return None, 0.0
        return result, total_conf / count


def main():
    parser = argparse.ArgumentParser(description="Plate Detection v2 (YOLO+OCR)")
    parser.add_argument("--device", default="0", help="Camera ID or stream URL")
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--model", default=None, help="Path to YOLO .pt model")
    parser.add_argument("--conf", type=float, default=0.4)
    parser.add_argument("--image", default=None, help="Test on single image (no camera)")
    args = parser.parse_args()

    # Image mode: test on single file, no camera needed
    if args.image:
        print("Testing on image:", args.image)
        detector = PlateDetectorYOLO(model_path=args.model, conf_threshold=args.conf)
        frame = cv2.imread(args.image)
        if frame is None:
            print(f"Cannot read image: {args.image}")
            return

        # Debug: run raw YOLO to see what it detects
        print("\n  [DEBUG] Raw YOLO detections:")
        raw_results = detector.model(frame, verbose=False, conf=0.1)
        for r in raw_results:
            if r.boxes is not None:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cls_name = detector.model.names.get(cls_id, f"class_{cls_id}")
                    print(f"    class={cls_id} ({cls_name}) conf={conf:.2f} box=({x1},{y1},{x2},{y2})")

        detections = detector.detect(frame)
        if not detections:
            print("\n  No plates detected after OCR pipeline. Try --conf 0.1")
        for (text, conf, (x1,y1,x2,y2)) in detections:
            print(f"  [{conf:.0%}] {text} | box=({x1},{y1},{x2},{y2})")
            cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 2)
        cv2.imwrite("/tmp/plate-v2-result.png", frame)
        print(f"  Result saved to /tmp/plate-v2-result.png")
        return

    source = int(args.device) if args.device.isdigit() else args.device
    is_stream = isinstance(source, str)

    print("=" * 50)
    print("  Plate Detection v2 - YOLO + EasyOCR")
    print("=" * 50)

    detector = PlateDetectorYOLO(model_path=args.model, conf_threshold=args.conf)

    if is_stream:
        grabber = FrameGrabber(source)
        time.sleep(3)
        ret, _ = grabber.read()
        if not ret:
            print("Cannot connect")
            grabber.release()
            return
    else:
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            print(f"Cannot open camera {source}")
            return
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print(f"Interval: {args.interval}s | Controls: q=quit, s=save, r=reset")
    last_detect = 0
    plate_text, plate_confidence = "", 0.0
    best_plates = {}

    while True:
        ret, frame = (grabber.read() if is_stream else cap.read())
        if not ret or frame is None:
            time.sleep(0.05)
            continue

        now = time.time()
        display = frame.copy()

        if now - last_detect >= args.interval:
            last_detect = now
            for (text, conf, (x1,y1,x2,y2)) in detector.detect(frame):
                cv2.rectangle(display, (x1,y1), (x2,y2), (0,255,0), 2)
                best_plates[text] = best_plates.get(text, 0) + 1
                if conf > plate_confidence or best_plates.get(text, 0) >= 2:
                    plate_text, plate_confidence = text, conf
                    print(f"  [{conf:.0%}] {text} (votes: {best_plates[text]})")
                    try:
                        from interfaces.cmd.gate_client import validate_and_open
                        validate_and_open(plate_text, plate_confidence, best_plates[text])
                    except Exception:
                        pass
            if len(best_plates) > 10:
                best_plates = dict(sorted(best_plates.items(), key=lambda x: x[1], reverse=True)[:5])

        if plate_text:
            cv2.rectangle(display, (5,5), (500,55), (0,0,0), -1)
            cv2.putText(display, f"{plate_text} ({plate_confidence:.0%})",
                        (10,40), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0,255,0), 2)

        cv2.imshow("Plate v2 (YOLO+OCR)", display)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:
            break
        elif key == ord("s"):
            cv2.imwrite(f"/tmp/plate-v2-{int(now)}.png", frame)
            print("  Saved!")
        elif key == ord("r"):
            plate_text, plate_confidence, best_plates = "", 0.0, {}
            print("  Reset!")

    (grabber.release() if is_stream else cap.release())
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Indonesian Plate Detection v6 - EasyOCR Improved
- Preprocessing optimized for white plate + black text (Mandatory font)
- Multi-read: OCR full frame + OCR cropped plate region for better accuracy
- Confidence voting: keeps best result across multiple reads
- Plate format correction with position-aware char fixing

Usage:
  python3 src/live_easyocr.py
  python3 src/live_easyocr.py --device "http://192.168.100.38:8080/video"
"""

import cv2
import easyocr
import numpy as np
import argparse
import time
import re
import threading
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plate_format import format_plate


class FrameGrabber:
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


def preprocess_for_plate(frame):
    """
    Preprocess frame to enhance plate readability.
    White plate + black text optimization.
    """
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Increase contrast with CLAHE (adaptive histogram equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    # Convert back to BGR (EasyOCR expects color or gray)
    return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)


def is_plate_candidate(text, bbox, all_results=None):
    """Check if detected text + bounding box looks like a plate"""
    clean = re.sub(r'[^A-Z0-9]', '', text.upper())

    # Length check: Indonesian plate = 4-10 chars
    if len(clean) < 4 or len(clean) > 12:
        return False

    # Must have mix of letters and digits
    has_letter = any(c.isalpha() for c in clean)
    has_digit = any(c.isdigit() for c in clean)
    if not (has_letter and has_digit):
        return False

    # Check bounding box aspect ratio (plate is wide)
    pts = np.array(bbox)
    width = np.linalg.norm(pts[1] - pts[0])
    height = np.linalg.norm(pts[3] - pts[0])
    if height == 0:
        return False
    ratio = width / height

    # REJECT: date/month patterns (e.g. "05-2027", "122027", "052027")
    # These are the expiry date below the plate number
    if re.match(r"^\d{2,4}$", clean):  # pure numbers like 2027, 0527
        return False
    if re.match(r"^\d{6,8}$", clean):  # date-like: 052027, 05122027
        return False
    # Reject if text is only 2-4 digits (month/year)
    if len(clean) <= 4 and clean.isdigit():
        return False
    # Reject common date patterns
    if re.match(r"^\d{1,2}(0[1-9]|1[0-2])\d{2,4}$", clean):
        return False

    # Indonesian plate MUST have a letter in first 2 chars (area code)
    first_two = clean[:2]
    if not any(c.isalpha() for c in first_two):
        return False

    # Plate text region should be wider than tall (ratio > 1.5)
    if ratio < 1.2:
        return False

    return True



def merge_horizontal_texts(results, y_threshold=40):
    """
    Merge text detections that are on the same horizontal line.
    Indonesian plates have spaced chars: "F  6797  OB" detected as 3 separate texts.
    This merges them into one: "F6797OB"
    """
    if not results:
        return results
    
    # Sort by vertical center (y), then horizontal (x)
    def get_center_y(r):
        pts = np.array(r[0])
        return pts[:, 1].mean()
    
    def get_min_x(r):
        pts = np.array(r[0])
        return pts[:, 0].min()
    
    sorted_results = sorted(results, key=lambda r: (get_center_y(r), get_min_x(r)))
    
    merged = []
    current_group = [sorted_results[0]]
    
    for i in range(1, len(sorted_results)):
        prev_y = get_center_y(current_group[-1])
        curr_y = get_center_y(sorted_results[i])
        
        if abs(curr_y - prev_y) < y_threshold:
            current_group.append(sorted_results[i])
        else:
            merged.append(current_group)
            current_group = [sorted_results[i]]
    merged.append(current_group)
    
    # Combine each group into single result
    combined = []
    for group in merged:
        if len(group) == 1:
            combined.append(group[0])
        else:
            # Merge: combine text, use outer bbox, average confidence
            all_text = "".join([r[1] for r in group])
            all_conf = sum([r[2] for r in group]) / len(group)
            # Build merged bbox (outer bounds)
            all_pts = np.concatenate([np.array(r[0]) for r in group])
            x_min, y_min = all_pts.min(axis=0)
            x_max, y_max = all_pts.max(axis=0)
            merged_bbox = [[x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max]]
            combined.append((merged_bbox, all_text, all_conf))
    
    return combined

def crop_plate_region(frame, bbox, padding=15):
    """Crop and straighten plate region from bounding box"""
    pts = np.array(bbox, dtype=np.int32)
    x_min = max(0, pts[:, 0].min() - padding)
    x_max = min(frame.shape[1], pts[:, 0].max() + padding)
    y_min = max(0, pts[:, 1].min() - padding)
    y_max = min(frame.shape[0], pts[:, 1].max() + padding)
    return frame[y_min:y_max, x_min:x_max]


def main():
    parser = argparse.ArgumentParser(description='Indonesian Plate Detection v6')
    parser.add_argument('--device', default='0', help='Camera ID or URL')
    parser.add_argument('--interval', type=float, default=3.0, help='OCR interval')
    parser.add_argument('--image', default=None, help='Test on single image file')
    args = parser.parse_args()

    print("Loading EasyOCR model...")
    reader = easyocr.Reader(['en'], gpu=False)
    print("Model loaded!")

    # Image mode: test on single file
    if args.image:
        print(f"Testing on image: {args.image}")
        frame = cv2.imread(args.image)
        if frame is None:
            print(f"Cannot read: {args.image}")
            return
        processed = preprocess_for_plate(frame)
        results = reader.readtext(processed, paragraph=False, min_size=20,
                                  text_threshold=0.5, low_text=0.3)
        if results:
            results = merge_horizontal_texts(results)
        print(f"\n  All OCR results:")
        for (bbox, text, conf) in results:
            clean = re.sub(r'[^A-Z0-9]', '', text.upper())
            fmt = format_plate(clean) if len(clean) >= 4 else None
            is_plate = is_plate_candidate(text, bbox)
            marker = "✅" if is_plate else "  "
            print(f"  {marker} [{conf:.0%}] '{text}' -> {fmt or clean}")
        print()
        return

    source = int(args.device) if args.device.isdigit() else args.device
    is_stream = isinstance(source, str)

    if is_stream:
        grabber = FrameGrabber(source)
        print(f"Connecting to: {source}")
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
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("Plate Detection v6 - q=quit, s=save")
    last_ocr = 0
    plate_text = ""
    plate_confidence = 0
    best_plates = {}  # voting: {plate: count}

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

        if now - last_ocr >= args.interval:
            last_ocr = now

            # Step 1: Preprocess frame for better contrast
            processed = preprocess_for_plate(frame)

            # Step 2: Run EasyOCR on processed frame
            results = reader.readtext(
                processed,
                
                paragraph=False,
                min_size=20,
                text_threshold=0.5,
                low_text=0.3,
            )

            # Merge texts on same horizontal line (e.g. "F" + "6797" + "OB" -> "F6797OB")
            if results:
                results = merge_horizontal_texts(results)
            for (bbox, text, conf) in results:
                if conf < 0.1:
                    continue

                if not is_plate_candidate(text, bbox):
                    continue

                clean = re.sub(r'[^A-Z0-9]', '', text.upper())

                # Draw bounding box on display
                pts = [[int(p[0]), int(p[1])] for p in bbox]
                cv2.polylines(display, [np.array(pts)], True, (0, 255, 0), 2)


                # Step 4: Format plate
                if len(clean) >= 4:
                    formatted = format_plate(clean)
                    result = formatted if formatted else clean

                    # Voting: track repeated detections
                    best_plates[result] = best_plates.get(result, 0) + 1

                    if conf > plate_confidence or best_plates.get(result, 0) >= 2:
                        plate_text = result
                        plate_confidence = conf
                        print(f"  [{conf:.0%}] Raw: {clean} -> {plate_text} (votes: {best_plates[result]})")

                        # Auto-validate & open gate when votes threshold reached
                        try:
                            from interfaces.cmd.gate_client import validate_and_open
                            validate_and_open(plate_text, plate_confidence, best_plates[result])
                        except Exception:
                            pass  # API not running or not imported

            # Decay old votes
            if len(best_plates) > 10:
                best_plates = dict(sorted(best_plates.items(), key=lambda x: x[1], reverse=True)[:5])

        # Show plate text
        if plate_text:
            cv2.rectangle(display, (5, 5), (450, 50), (0, 0, 0), -1)
            cv2.putText(display, f"{plate_text} ({plate_confidence:.0%})", (10, 38),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 0), 2)

        cv2.imshow("Plate v6", display)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif key == ord('s'):
            cv2.imwrite(f"/tmp/plate-{int(now)}.png", frame)
            print("  Saved!")
        elif key == ord('r'):
            plate_text = ""
            plate_confidence = 0
            best_plates = {}
            print("  Reset!")

    if is_stream:
        grabber.release()
    else:
        cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

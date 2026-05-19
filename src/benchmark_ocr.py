#!/usr/bin/env python3
"""
Benchmark: EasyOCR vs PaddleOCR on same image.

Usage:
  python3 src/benchmark_ocr.py --image /tmp/plate-v2-1779203140.png

Install PaddleOCR:
  pip3 install --break-system-packages paddlepaddle paddleocr
"""

import cv2
import re
import time
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plate_format import format_plate


def preprocess(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)


def test_easyocr(processed):
    import easyocr
    print("\n" + "=" * 50)
    print("  EasyOCR")
    print("=" * 50)

    reader = easyocr.Reader(["en"], gpu=False, verbose=False)

    t = time.time()
    results = reader.readtext(processed, paragraph=False, min_size=20,
                              text_threshold=0.5, low_text=0.3)
    elapsed = time.time() - t

    print(f"  Time: {elapsed:.2f}s")
    print(f"  Results:")
    for (bbox, text, conf) in results:
        clean = re.sub(r"[^A-Z0-9]", "", text.upper())
        if len(clean) >= 3:
            fmt = format_plate(clean) if len(clean) >= 4 else None
            print(f"    [{conf:.0%}] '{text}' -> {fmt or clean}")

    return elapsed


def test_paddleocr(processed):
    try:
        from paddleocr import PaddleOCR
    except ImportError:
        print("\n  PaddleOCR not installed. Run:")
        print("  pip3 install --break-system-packages paddlepaddle paddleocr")
        return None

    print("\n" + "=" * 50)
    print("  PaddleOCR")
    print("=" * 50)

    ocr = PaddleOCR(lang="en")

    t = time.time()
    results = ocr.ocr(processed)
    elapsed = time.time() - t

    print(f"  Time: {elapsed:.2f}s")
    print(f"  Results:")
    if results and results[0]:
        for line in results[0]:
            bbox, (text, conf) = line[0], line[1]
            clean = re.sub(r"[^A-Z0-9]", "", text.upper())
            if len(clean) >= 3:
                fmt = format_plate(clean) if len(clean) >= 4 else None
                print(f"    [{conf:.0%}] '{text}' -> {fmt or clean}")

    return elapsed


def main():
    parser = argparse.ArgumentParser(description="OCR Benchmark")
    parser.add_argument("--image", required=True, help="Image file path")
    args = parser.parse_args()

    frame = cv2.imread(args.image)
    if frame is None:
        print(f"Cannot read: {args.image}")
        return

    print(f"Image: {args.image} ({frame.shape[1]}x{frame.shape[0]})")
    processed = preprocess(frame)

    t1 = test_easyocr(processed)
    t2 = test_paddleocr(processed)

    print("\n" + "=" * 50)
    print("  SUMMARY")
    print("=" * 50)
    print(f"  EasyOCR:   {t1:.2f}s")
    if t2:
        print(f"  PaddleOCR: {t2:.2f}s")
        print(f"  Winner:    {'PaddleOCR' if t2 < t1 else 'EasyOCR'} ({abs(t1-t2):.1f}s faster)")


if __name__ == "__main__":
    main()

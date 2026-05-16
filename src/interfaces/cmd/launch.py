"""
CMD Launch - Live OCR plate detection from camera.
Wraps the existing live_easyocr.py as a proper interface.

Usage:
  INTERFACE=CMD python src/main.py
  INTERFACE=CMD python src/main.py -- --device "rtsp://..."
  INTERFACE=CMD python src/main.py -- --interval 3
"""

import sys
import os

# Ensure src is in path
src_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, src_dir)

from live_easyocr import main as ocr_main


def launch():
    """Launch live OCR detection (delegates to live_easyocr)."""
    ocr_main()

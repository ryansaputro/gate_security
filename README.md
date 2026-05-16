# OCR Live - Indonesian License Plate Detection

Live plate number detection system for Indonesian vehicles (TNKB).

## Structure

```
ocr-live/
├── src/
│   ├── plate_format.py    # Indonesian plate format corrector
│   └── live_easyocr.py    # Main app (EasyOCR - recommended)
├── misc/
│   └── ceshi.ini          # V380 RTSP enabler (for reference)
├── requirements.txt
├── .gitignore
└── README.md
```

## Setup

```bash
# Install dependencies (CPU-only PyTorch)
pip3 install --break-system-packages -r requirements.txt \
  --extra-index-url https://download.pytorch.org/whl/cpu

# Additional deps for EasyOCR
pip3 install --break-system-packages python-bidi pyclipper ninja scipy scikit-image shapely
```

## Usage

```bash
# Webcam (default device 0)
python3 src/live_easyocr.py

# IP Webcam (Android app)
python3 src/live_easyocr.py --device "http://192.168.x.x:8080/video"

# RTSP (CCTV)
python3 src/live_easyocr.py --device "rtsp://user:pass@192.168.x.x:554/live/ch00_0"

# Adjust OCR interval (default 2s)
python3 src/live_easyocr.py --interval 3
```

## Controls

- `q` / `ESC` - Quit
- `s` - Save current frame to /tmp

## Plate Format

Indonesian plate: `[A-Z]{1,2} [0-9]{1,4} [A-Z]{1,3}`

Examples: `B 1234 XYZ`, `AB 12 C`, `D 1 ABC`

The system auto-corrects OCR misreads based on position context
(e.g., `0` in letter position becomes `O`, `Z` in number position becomes `2`).

## Notes

- First run downloads EasyOCR model (~100MB, cached after)
- Requires ~1.5GB RAM during runtime
- Works best with plate clearly visible and well-lit

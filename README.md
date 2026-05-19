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

### System Dependencies (Ubuntu/Debian)

```bash
# Required for OpenCV GUI (camera preview window)
sudo apt install -y libgtk-3-0 libgtk-3-dev

# Required for MongoDB
sudo apt install -y mongodb-org
# Or use Docker: docker run -d -p 27017:27017 mongo:7

# Python 3.10+
sudo apt install -y python3 python3-pip python3-full
```

### Python Dependencies

```bash
# API only (no OCR)
pip3 install --break-system-packages -r requirements.txt

# Full install with OCR + YOLO (for plate detection)
pip3 install --break-system-packages -r requirements.txt \
  --extra-index-url https://download.pytorch.org/whl/cpu
pip3 install --break-system-packages python-bidi pyclipper ninja scipy scikit-image shapely

# If cv2.imshow error (GTK not found):
pip3 install --break-system-packages --force-reinstall opencv-python
```

## Usage

### HTTP API Server

```bash
make local-http
# Swagger: http://localhost:3000/docs
```

### Plate Detection v1 (EasyOCR only)

```bash
# Webcam (default device 0)
python3 src/live_easyocr.py

# IP Webcam (Android app)
python3 src/live_easyocr.py --device "http://192.168.x.x:8080/video"

# RTSP (CCTV)
python3 src/live_easyocr.py --device "rtsp://user:pass@192.168.x.x:554/live/ch00_0"
```

### Plate Detection v2 (YOLO + EasyOCR)

```bash
# With custom trained model (best accuracy)
make local-cmd-v2-model MODEL=models/plate_best.pt

# With stream
make local-cmd-v2-stream MODEL=models/plate_best.pt DEVICE="rtsp://..." INTERVAL=1

# Without model (generic YOLO, fallback to contour detection)
make local-cmd-v2
```

### Plate Detection v3 (YOLO + PaddleOCR) — Recommended, Fastest

~4-5x faster than v2 (EasyOCR). Same accuracy, much lower latency.

#### v3 Dependencies

```bash
# System (Ubuntu/Debian)
sudo apt install -y libgtk-3-0 libgtk-3-dev python3 python3-pip

# Python packages (MUST use these exact versions to avoid ABI conflicts)
pip3 install --break-system-packages --force-reinstall \
  numpy==1.26.4 \
  opencv-python==4.10.0.84 \
  paddlepaddle==2.6.2 \
  paddleocr==2.9.1 \
  ultralytics

# Or use Makefile shortcut:
make fix-gui
make install-paddle
```

#### v3 Usage

```bash
# Webcam with GUI window
make local-cmd-v3

# Webcam headless (terminal only, no window)
make local-cmd-v3-headless

# With custom YOLO model
make local-cmd-v3-model MODEL=models/plate_best.pt

# RTSP/IP stream
make local-cmd-v3-stream MODEL=models/plate_best.pt DEVICE="rtsp://..." INTERVAL=1

# Test on single image
make local-cmd-v3-image MODEL=models/plate_best.pt IMAGE=/tmp/plate.png
```

#### v3 Controls (GUI mode)

- `q` / `ESC` - Quit
- `s` - Save current frame to /tmp
- `r` - Reset plate detection

#### v3 Notes

- First run downloads PaddleOCR model (~30MB, cached after)
- Requires ~800MB RAM (vs ~1.5GB for EasyOCR)
- Detection speed: ~0.2s per frame (vs ~0.9s EasyOCR)
- If GUI crashes with GTK error, run `make fix-gui` first

### CRON Scheduler (Dues Reminder)

```bash
make local-cron
```

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

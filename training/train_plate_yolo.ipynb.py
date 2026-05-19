"""
=============================================================
YOLO Plate Detection Training Script
=============================================================
Run this in Google Colab (free GPU):
1. Go to https://colab.research.google.com
2. New Notebook
3. Runtime → Change runtime type → GPU (T4)
4. Copy-paste each cell below

Dataset: Roboflow public Indonesian license plate dataset
Model: YOLOv8n (nano - optimized for Raspberry Pi)
=============================================================
"""

# ============ CELL 1: Install dependencies ============
# !pip install ultralytics roboflow

# ============ CELL 2: Download dataset from Roboflow ============
"""
Option A: Use Roboflow API (recommended - auto downloads labeled data)
1. Go to https://universe.roboflow.com
2. Search: "Indonesian license plate" or "license plate detection"
3. Pick a dataset with 500+ images
4. Click "Download" → YOLOv8 format → Get API snippet

Good datasets to use:
- "License Plate Recognition" by roboflow-universe-projects (~24k images)
- "license-plate-detector" (general, works for Indonesian plates too)
- "Indonesian Vehicle Plate" (if available)

Paste the Roboflow download code below:
"""

# from roboflow import Roboflow
# rf = Roboflow(api_key="YOUR_API_KEY")  # Get from roboflow.com/settings
# project = rf.workspace("YOUR_WORKSPACE").project("YOUR_PROJECT")
# version = project.version(1)
# dataset = version.download("yolov8")

# --- OR Option B: Use a known public dataset ---
# This uses a general license plate dataset that works well:

# from roboflow import Roboflow
# rf = Roboflow(api_key="YOUR_API_KEY")
# project = rf.workspace("roboflow-universe-projects").project("license-plate-recognition-rxg4e")
# version = project.version(4)
# dataset = version.download("yolov8")


# ============ CELL 3: Train YOLOv8n ============
"""
from ultralytics import YOLO

# Load YOLOv8 nano (smallest, fastest - perfect for Pi)
model = YOLO("yolov8n.pt")

# Train
# Adjust 'data' path to match your downloaded dataset
results = model.train(
    data=f"{dataset.location}/data.yaml",  # or manual path
    epochs=100,
    imgsz=640,
    batch=16,
    name="plate_detector_indo",
    patience=20,        # early stopping
    optimizer="AdamW",
    lr0=0.001,
    augment=True,
    mosaic=1.0,
    flipud=0.0,         # don't flip plates upside down
    fliplr=0.5,         # horizontal flip OK
    degrees=5.0,        # slight rotation
    translate=0.1,
    scale=0.3,
    hsv_h=0.015,
    hsv_s=0.5,
    hsv_v=0.3,
)
"""


# ============ CELL 4: Evaluate ============
"""
# Validate on test set
metrics = model.val()
print(f"mAP50: {metrics.box.map50:.3f}")
print(f"mAP50-95: {metrics.box.map:.3f}")

# Should see mAP50 > 0.85 for good plate detection
"""


# ============ CELL 5: Export & Download ============
"""
import shutil
from google.colab import files

# Best model is at:
best_model = "runs/detect/plate_detector_indo/weights/best.pt"

# Copy to easy location
shutil.copy(best_model, "/content/plate_best.pt")

# Download to your computer
files.download("/content/plate_best.pt")

print("Done! Place plate_best.pt in tools/ocr-live/models/")
print("Then run: python3 src/live_yolo_ocr.py --model models/plate_best.pt")
"""


# ============ CELL 6 (Optional): Test on sample image ============
"""
from ultralytics import YOLO
from google.colab.patches import cv2_imshow
import cv2

model = YOLO("/content/plate_best.pt")

# Test on a sample image
results = model("path/to/test_image.jpg", conf=0.4)

# Show results
for r in results:
    img = r.plot()
    cv2_imshow(img)
    
    # Print detections
    for box in r.boxes:
        conf = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        print(f"  Plate detected: conf={conf:.2f}, box=({x1},{y1},{x2},{y2})")
"""


# ============ CELL 7 (Optional): Export to ONNX for faster Pi inference ============
"""
from ultralytics import YOLO

model = YOLO("/content/plate_best.pt")

# Export to ONNX (faster inference on CPU/Pi)
model.export(format="onnx", imgsz=640, simplify=True)

from google.colab import files
files.download("runs/detect/plate_detector_indo/weights/best.onnx")
"""

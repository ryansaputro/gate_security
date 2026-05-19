# Training YOLOv8n for Plate Detection

## Why Custom Model?

The generic YOLOv8n detects vehicles (car, truck, motorcycle) but not plates directly.
A custom model trained on plate images gives you:
- Direct plate bounding box (no contour detection needed)
- 95%+ accuracy even at night/rain
- Faster inference (~30ms vs ~100ms with contour fallback)

## Quick Start (Google Colab - Free GPU)

### 1. Collect Images

Take 200-500 photos from your gate camera:
- Different times of day (morning, noon, night)
- Different vehicles (car, motorcycle)
- Different angles
- Include some with no plate visible (negative samples)

### 2. Label with Roboflow (Free)

1. Go to https://roboflow.com (free account)
2. Create project → Object Detection
3. Upload images
4. Draw bounding box around each plate
5. Export → YOLOv8 format → Download zip

### 3. Train on Google Colab

```python
# In Google Colab (free GPU)
!pip install ultralytics

from ultralytics import YOLO

# Load base model
model = YOLO("yolov8n.pt")

# Train (adjust path to your dataset)
model.train(
    data="/content/dataset/data.yaml",
    epochs=100,
    imgsz=640,
    batch=16,
    name="plate_detector",
)

# Export best model
# Download: runs/detect/plate_detector/weights/best.pt
```

Training takes ~30-60 minutes on Colab free GPU.

### 4. Use Custom Model

```bash
# Copy best.pt to your Pi
python3 src/live_yolo_ocr.py --model models/plate_best.pt

# Or via Makefile
make local-cmd-v2-model MODEL=models/plate_best.pt
```

## Tips for Better Accuracy

- Include at least 50 night images
- Label plates even if partially visible
- Include motorcycle plates (smaller, different ratio)
- Augmentation: Roboflow auto-applies rotation, blur, brightness
- More data > more epochs (200 images minimum, 500 ideal)

## Without Custom Model

The v2 script works without a custom model by:
1. Detecting vehicles with generic YOLOv8n
2. Finding plate region within vehicle box using OpenCV contours
3. Running OCR on the detected region

This is less accurate but requires zero training.

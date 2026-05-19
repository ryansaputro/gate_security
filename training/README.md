# Training YOLO Plate Detector

## Persiapan (5 menit)

### 1. Buat Roboflow Account
1. Buka https://app.roboflow.com
2. Klik "Sign Up" (pakai Google biar cepet)
3. Setelah masuk, klik avatar kanan atas → **Settings**
4. Di sidebar kiri, klik **Roboflow API Key**
5. Copy API key-nya (simpan di notepad dulu)

### 2. Buka Google Colab
1. Buka https://colab.research.google.com
2. Klik **"New Notebook"**
3. Di menu atas, klik **Runtime** → **Change runtime type**
4. Pilih **T4 GPU** → klik **Save**

---

## Training (30-60 menit)

### Cell 1: Install Library

Klik di cell kosong, paste code ini, tekan **Shift+Enter**:

```python
!pip install ultralytics roboflow -q
```

Tunggu sampai selesai (~1 menit). Ada warning bisa diabaikan.

---

### Cell 2: Download Dataset

Klik **+ Code** (tombol di atas), paste ini, **GANTI** `YOUR_KEY` dengan API key Roboflow lo:

```python
from roboflow import Roboflow

# GANTI YOUR_KEY dengan API key dari Roboflow Settings
rf = Roboflow(api_key="YOUR_KEY")

# Download dataset plat nomor (24k+ gambar, gratis)
project = rf.workspace("roboflow-universe-projects").project("license-plate-recognition-rxg4e")
version = project.version(4)
dataset = version.download("yolov8")

print(f"\n✅ Dataset downloaded to: {dataset.location}")
print(f"   Train images: check!")
```

Tekan **Shift+Enter**. Tunggu download selesai (~2-3 menit).

---

### Cell 3: Mulai Training

Klik **+ Code**, paste ini:

```python
from ultralytics import YOLO

# Load YOLOv8 nano (paling kecil & cepat, cocok buat Raspberry Pi)
model = YOLO("yolov8n.pt")

# Train! Ini yang lama (30-60 menit)
results = model.train(
    data=f"{dataset.location}/data.yaml",
    epochs=100,        # jumlah iterasi training
    imgsz=640,         # ukuran gambar
    batch=16,          # batch size
    name="plate_indo", # nama project
    patience=20,       # stop otomatis kalau udah ga improve
    optimizer="AdamW",
    augment=True,      # augmentasi data (flip, rotate, dll)
)

print("\n✅ Training selesai!")
print(f"   Best mAP50: {results.results_dict.get('metrics/mAP50(B)', 'N/A')}")
```

Tekan **Shift+Enter**.

**TUNGGU 30-60 MENIT.** Lo bisa:
- Buka tab lain (jangan close tab Colab)
- Scroll ke bawah buat liat progress (epoch 1/100, 2/100, dst)
- Kalau ada tulisan "EarlyStopping" berarti selesai lebih cepat (bagus)

---

### Cell 4: Cek Hasil

Setelah training selesai, klik **+ Code**, paste:

```python
from ultralytics import YOLO

# Load model terbaik
best_model = YOLO("runs/detect/plate_indo/weights/best.pt")

# Validasi
metrics = best_model.val()

print("\n" + "="*50)
print("  HASIL TRAINING")
print("="*50)
print(f"  mAP50:    {metrics.box.map50:.3f}")
print(f"  mAP50-95: {metrics.box.map:.3f}")
print(f"  Precision: {metrics.box.mp:.3f}")
print(f"  Recall:    {metrics.box.mr:.3f}")
print("="*50)

if metrics.box.map50 > 0.85:
    print("  🎉 BAGUS! Model siap dipakai.")
elif metrics.box.map50 > 0.70:
    print("  👍 Cukup bagus. Bisa improve nanti dengan data dari gate sendiri.")
else:
    print("  ⚠️  Kurang bagus. Coba tambah epochs atau pakai dataset lain.")
```

Shift+Enter.

---

### Cell 5: Download Model

Klik **+ Code**, paste:

```python
import shutil
from google.colab import files

# Copy best model
shutil.copy("runs/detect/plate_indo/weights/best.pt", "/content/plate_best.pt")

# Cek ukuran
import os
size_mb = os.path.getsize("/content/plate_best.pt") / (1024*1024)
print(f"Model size: {size_mb:.1f} MB")

# Download ke laptop lo
files.download("/content/plate_best.pt")
print("\n✅ File plate_best.pt sedang di-download ke laptop lo!")
```

Shift+Enter. Browser akan download file `plate_best.pt` (~6MB).

---

## Deploy ke Project (2 menit)

### Di laptop/PC lo:

```bash
# 1. Pindahkan model ke folder project
mkdir -p tools/ocr-live/models
mv ~/Downloads/plate_best.pt tools/ocr-live/models/

# 2. Test jalankan (pakai webcam)
cd tools/ocr-live
python3 src/live_yolo_ocr.py --model models/plate_best.pt

# 3. Atau pakai stream
python3 src/live_yolo_ocr.py --model models/plate_best.pt --device "http://192.168.1.x:8080/video"
```

---

## Troubleshooting

| Problem | Solusi |
|---------|--------|
| "API key invalid" | Cek ulang key di Roboflow Settings |
| "Runtime disconnected" | Reconnect, jalankan ulang dari Cell 3 |
| "Out of memory" | Kurangi batch jadi 8: `batch=8` |
| mAP50 < 0.7 | Tambah epochs jadi 150: `epochs=150` |
| Download ga jalan | Klik kanan file di panel kiri Colab → Download |

## Nanti: Fine-tune dengan Data Gate Sendiri

Setelah deploy, kumpulin 50-100 foto dari gate lo:
1. Jalankan OCR, setiap deteksi auto-save frame (tekan `s`)
2. Upload ke Roboflow, label plate box-nya
3. Re-train dengan dataset campuran (public + gate lo)
4. Akurasi naik dari ~85% ke ~95%+

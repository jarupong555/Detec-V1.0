import os
from pathlib import Path
from dotenv import load_dotenv

# หา path ของ .env อัตโนมัติ (อยู่ข้างนอก backend)
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR.parent / ".env"

# โหลด .env ถ้ามี
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    print(f".env not found at {ENV_PATH}")

# โฟลเดอร์หลัก
DATA_DIR = BASE_DIR / "data"
SAVED_DIR = DATA_DIR / "saved"

# ตัวแปรจาก .env
DETECT_CLASSES = os.getenv("DETECT_CLASSES", "person")
MAX_SAVED = int(os.getenv("MAX_SAVED", "30"))
MODEL_NAME = os.getenv("MODEL_NAME", "yolov8l.pt")
CONF_THRES = float(os.getenv("CONF_THRES", "0.25"))
IOU_THRES = float(os.getenv("IOU_THRES", "0.45"))
DEVICE = os.getenv("DEVICE", "cpu")
NOTIFY_URL = os.getenv("NOTIFY_URL", "").strip()
TZ = os.getenv("TZ", "Asia/Bangkok")
DETECT_EVERY_N = int(os.getenv("DETECT_EVERY_N", "1"))
MAX_SAVED_PER_FOLDER = int(os.getenv("MAX_SAVED_PER_FOLDER", "0"))

# ไฟล์ JSON เก็บ config กล้อง
CAMERAS_JSON = DATA_DIR / "cameras.json"

# สร้างโฟลเดอร์ถ้ายังไม่มี
for d in [DATA_DIR, SAVED_DIR]:
    d.mkdir(parents=True, exist_ok=True)

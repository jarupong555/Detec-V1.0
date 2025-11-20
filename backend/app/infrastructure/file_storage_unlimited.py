# -->> detection_service.py

from pathlib import Path
from datetime import datetime
from ..core.config import SAVED_DIR
from ..core.logger import get_logger

log = get_logger("file_storage_unlimited")

def sanitize_filename(name: str) -> str:
    """
    ลบหรือแทนที่อักขระต้องห้ามในชื่อไฟล์ เช่น :, /, \ เป็นต้น
    """
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for ch in invalid_chars:
        name = name.replace(ch, '-')
    return name.strip() or "unknown"


def ensure_camera_dir(location: str) -> Path:
    """
    สร้างโฟลเดอร์ตามชื่อ location (ถ้าไม่มีให้ใช้ unknown)
    """
    loc = sanitize_filename(location or "unknown")
    d = SAVED_DIR / loc
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_frame(location: str, filename: str, jpg_bytes: bytes) -> Path:
    """
     บันทึกภาพโดยไม่จำกัดจำนวน (ไม่ลบอัตโนมัติ)
    """
    d = ensure_camera_dir(location)
    timestamp = datetime.now().strftime("%Y%m%d_%H-%M-%S")
    fname = sanitize_filename(f"{filename}_{timestamp}.jpg")

    out = d / fname
    with open(out, "wb") as f:
        f.write(jpg_bytes)

    log.info(f"[UNLIMITED] Saved frame: {out}")
    return out


def list_saved(location: str):
    """
    คืนลิสต์ไฟล์ทั้งหมดในโฟลเดอร์ (ไม่ลบใดๆ)
    """
    d = ensure_camera_dir(location)
    return sorted(d.glob("*.jpg"), key=lambda x: x.stat().st_mtime)

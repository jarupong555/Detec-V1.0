from pathlib import Path
from typing import List
from datetime import datetime
from ..core.config import SAVED_DIR, MAX_SAVED, MAX_SAVED_PER_FOLDER
from ..core.logger import get_logger
import pytz
log = get_logger("file_storage")

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
    บันทึกภาพ และตรวจลบภาพเก่าถ้าเกิน limit
    """
    d = ensure_camera_dir(location)

    # ใช้เวลาไทย
    tz = pytz.timezone("Asia/Bangkok")
    timestamp = datetime.now(tz).strftime("%Y%m%d_%H-%M-%S")

    base = "_".join(filename.split("_")[:2])
    fname = sanitize_filename(f"{base}_{timestamp}.jpg")
    
    out = d / fname
    with open(out, "wb") as f:
        f.write(jpg_bytes)

    log.info(f"Saved frame {out}")
    prune_overflow(location)
    return out


def list_saved(location: str) -> List[Path]:
    """
    คืนลิสต์ไฟล์เรียงตามเวลาสร้าง (เก่าก่อน)
    """
    d = ensure_camera_dir(location)
    return sorted(d.glob("*.jpg"), key=lambda x: x.stat().st_mtime)


def prune_overflow(location: str):
    """
    ลบไฟล์เก่าถ้าเกินจำนวนสูงสุดที่กำหนดใน .env
    """
    # เลือกใช้ MAX_SAVED_PER_FOLDER ก่อน ถ้าไม่มีใช้ MAX_SAVED เดิม
    try:
        max_files = int(MAX_SAVED_PER_FOLDER)
    except Exception:
        max_files = int(MAX_SAVED)

    files = list_saved(location)
    overflow = len(files) - max_files

    if overflow > 0:
        log.info(f"Folder '{location}' has {len(files)} files, pruning {overflow} oldest...")
        for p in files[:overflow]:
            try:
                p.unlink(missing_ok=True)
                log.info(f"Deleted old file: {p.name}")
            except Exception as e:
                log.warning(f"Failed to delete {p}: {e}")

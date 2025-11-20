import cv2, time
import numpy as np
from datetime import datetime, timezone
from typing import List, Optional
from ..infrastructure.yolo_model import YoloDetector
from ..infrastructure.file_storage import save_frame
from ..infrastructure.notification_client import notify_saved
from ..core.logger import get_logger
from ..core.config import DETECT_CLASSES, DETECT_EVERY_N

log = get_logger("detection_service")


def parse_classes(names_map: dict, classes_str: str | None) -> Optional[List[int]]:
    if not classes_str:
        return []  # ไม่มี class = ไม่ detect อะไรเลย
    if classes_str.lower() == "all":
        return None  # all = detect ทุก class

    wanted = [c.strip().lower() for c in classes_str.split(",") if c.strip()]
    inv = {v.lower(): k for k, v in names_map.items()}
    idxs = []
    for w in wanted:
        if w.isdigit():
            idxs.append(int(w))
        elif w in inv:
            idxs.append(inv[w])
    return idxs


class DetectionService:
    def __init__(self, model: YoloDetector, stream_service):
        self.model = model
        self.stream_service = stream_service  # ✅ ใช้ตัวเดียวกับระบบหลัก
        self.last_saved_ts = {}
        self.frame_count = {}

    def process(self, cam: dict, frame_bgr: np.ndarray) -> tuple[bytes, list]:
        cam_id = cam["id"]

        # ถ้า worker หยุดแล้ว ไม่ต้อง detect
        worker = self.stream_service.workers.get(cam_id)
        if not worker or not worker.running:
            log.info(f"🧹 Skip detection: {cam_id} stream stopped")
            return b"", []

        self.frame_count[cam_id] = self.frame_count.get(cam_id, 0) + 1

        # fallback detect_classes
        classes_str = cam.get("detect_classes") or DETECT_CLASSES
        classes_filter = parse_classes(self.model.names, classes_str)

        # ตรวจเฉพาะทุกๆ DETECT_EVERY_N เฟรม
        if self.frame_count[cam_id] % DETECT_EVERY_N != 0:
            ok, jpg = cv2.imencode(".jpg", frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            return (jpg.tobytes() if ok else b""), []

        try:
            annotated, dets = self.model.detect(frame_bgr, classes_filter)
        except Exception as e:
            log.warning(f"YOLO detect error on {cam_id}: {e}")
            return b"", []

        ok, jpg = cv2.imencode(".jpg", annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ok:
            return b"", dets

        jpg_bytes = jpg.tobytes()

        # เซฟรูปทุก 5 วิ
        if dets:
            now = time.time()
            last = self.last_saved_ts.get(cam_id, 0)
            if now - last >= 5.0:
                self.last_saved_ts[cam_id] = now

                cls_name = dets[0][1]
                dt_utc = datetime.now(timezone.utc)
                timestamp = dt_utc.strftime("%Y%m%d_%H-%M-%S")
                fname = f"{cls_name}_{cam['name']}_{timestamp}"

                save_frame(cam.get("location") or cam_id, fname, jpg_bytes)
                notify_saved(fname, dt_utc)

        return jpg_bytes, dets

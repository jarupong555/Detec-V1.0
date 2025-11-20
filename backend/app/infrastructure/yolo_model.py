from typing import List, Tuple
import cv2
import numpy as np
from ultralytics import YOLO
from ..core.config import MODEL_NAME, CONF_THRES, IOU_THRES, DEVICE
from ..core.logger import get_logger
import time
import torch

log = get_logger("yolo_model")

class YoloDetector:
    def __init__(self):
        # ถ้าไม่มี GPU → ใช้โมเดลเล็ก
        model_to_load = "yolov8n.pt" if DEVICE == "cpu" else MODEL_NAME
        log.info(f"Loading YOLO model: {model_to_load} on {DEVICE}")
        self.model = YOLO(model_to_load)
        self.names = self.model.names
        self.frame_count = 0

        # ตรวจว่าใช้ GPU หรือ CPU
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            log.info(f"Using GPU: {gpu_name}")
        else:
            log.info("Using CPU only (no CUDA detected)")

    def detect(self, frame_bgr: np.ndarray, classes_filter: List[int] | None) -> Tuple[np.ndarray, list]:
        """
        ตรวจจับพร้อมติดตาม (YOLOv8 Tracking mode)
        """
        t0 = time.time()
        annotated = frame_bgr.copy()
        det_list = []

        try:
            # ใช้ tracker แต่ไม่จำ state เดิม (กัน crash ตอนปิด stream)
            results = self.model.track(
                source=frame_bgr,
                conf=CONF_THRES,
                iou=IOU_THRES,
                device=DEVICE,
                persist=False,     # ป้องกัน crash เวลา stream ปิด
                verbose=False
            )
        except Exception as e:
            log.warning(f"Tracker failed: {e} — fallback to predict()")
            results = self.model.predict(
                source=frame_bgr,
                conf=CONF_THRES,
                iou=IOU_THRES,
                device=DEVICE,
                verbose=False
            )

        # วาดผลลัพธ์
        for r in results:
            if not hasattr(r, "boxes") or r.boxes is None:
                continue

            for b in r.boxes:
                cls_id = int(b.cls)
                if classes_filter and cls_id not in classes_filter:
                    continue

                conf = float(b.conf)
                x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
                name = self.names.get(cls_id, str(cls_id))
                track_id = getattr(b, "id", None)

                # สีและขนาด
                color = (0, 255, 0) if track_id else (255, 0, 0)
                h, w, _ = annotated.shape
                thickness = max(1, int(min(h, w) / 1000))   # เส้นบางลง
                font_scale = min(h, w) / 500               # ตัวอักษรเล็กลงเล็กน้อย

                # วาดกรอบ
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)

                # ข้อความ
                label = f"{name} {int(track_id) if track_id else '-'} {conf:.2f}"

                cv2.putText(
                    annotated,
                    label,
                    (x1 + 2, max(20, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale,
                    color,
                    thickness,       # ลดจาก thickness + 1 → thickness
                    lineType=cv2.LINE_AA
                )

                det_list.append((cls_id, name, conf, (x1, y1, x2, y2), track_id))

        fps = 1.0 / (time.time() - t0)
        log.info(f"Detection + Tracking: {len(det_list)} objects ({fps:.1f} FPS)")
        return annotated, det_list

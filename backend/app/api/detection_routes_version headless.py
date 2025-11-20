from fastapi import APIRouter
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Iterator
import time
import os

from ..services.camera_service import CameraService
from ..services.stream_service import StreamService
from ..services.detection_service import DetectionService
from ..infrastructure.yolo_model import YoloDetector
from ..domain.models import CameraOut, DeleteResult
from ..core.logger import get_logger

router = APIRouter()
log = get_logger("routes")

camera_service = CameraService()
stream_service = StreamService()
detector = YoloDetector()
detection_service = DetectionService(detector)

# โหลดค่าจาก .env
CAMERA_LIST = os.getenv("CAMERA_LIST", "")
DEFAULT_CLASSES = os.getenv("DETECT_CLASSES", "person")

def _parse_camera_env():
    """
    🔹 อ่านค่ากล้องจาก .env
    รูปแบบ: name,location,protocol,source
    """
    cams = []
    if not CAMERA_LIST.strip():
        log.warning("No CAMERA_LIST found in .env")
        return cams

    for entry in CAMERA_LIST.split(";"):
        parts = [p.strip() for p in entry.split(",")]
        if len(parts) < 4:
            log.warning(f"Invalid CAMERA_LIST entry: {entry}")
            continue
        name, location, protocol, source = parts[:4]
        cams.append({
            "name": name,
            "location": location,
            "protocol": protocol,
            "source": source,
            "detect_classes": DEFAULT_CLASSES
        })
    return cams


INIT_CAMERAS = _parse_camera_env()
for cam in INIT_CAMERAS:
    camera_service.add(cam["name"], cam["location"], cam["protocol"], cam["source"], cam["detect_classes"])
log.info(f"Loaded {len(INIT_CAMERAS)} cameras from .env")

@router.get("/cameras", response_model=list[CameraOut])
def list_cameras():
    return camera_service.list()

@router.delete("/cameras/{cam_id}", response_model=DeleteResult)
def delete_camera(cam_id: str):
    ok = camera_service.delete(cam_id)
    stream_service.stop_worker(cam_id)
    return DeleteResult(ok=ok)

def mjpeg_generator(cam: dict) -> Iterator[bytes]:
    w = stream_service.ensure_worker(cam)
    boundary = b"--frame"
    while True:
        frame = w.get_latest()
        if frame is None:
            time.sleep(0.05)
            continue
        jpg_bytes, _dets = detection_service.process(cam, frame)
        if not jpg_bytes:
            continue
        yield boundary + b"\r\n" + b"Content-Type: image/jpeg\r\n\r\n" + jpg_bytes + b"\r\n"

@router.get("/stream/{cam_id}")
def stream_mjpeg(cam_id: str):
    cam = camera_service.get(cam_id)
    if not cam:
        return JSONResponse({"detail": "camera not found"}, status_code=404)
    return StreamingResponse(mjpeg_generator(cam), media_type="multipart/x-mixed-replace; boundary=frame")

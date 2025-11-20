
from fastapi import APIRouter
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Iterator
import time

from ..services.camera_service import CameraService
from ..services.stream_service import StreamService
from ..services.detection_service import DetectionService
from ..infrastructure.yolo_model import YoloDetector
from ..domain.models import CameraIn, CameraOut, ClassesConfig, DeleteResult
from ..core.logger import get_logger

router = APIRouter()
log = get_logger("routes")

camera_service = CameraService()
stream_service = StreamService()
detector = YoloDetector()
detection_service = DetectionService(detector, stream_service)

@router.get("/cameras", response_model=list[CameraOut])
def list_cameras():
    cams = camera_service.list()
    return cams

@router.post("/cameras", response_model=CameraOut, status_code=201)
def add_camera(cam: CameraIn):
    item = camera_service.add(cam.name, cam.location, cam.protocol, cam.source, cam.detect_classes)
    return item

@router.delete("/cameras/{cam_id}", response_model=DeleteResult)
def delete_camera(cam_id: str):
    ok = camera_service.delete(cam_id)
    stream_service.stop_worker(cam_id)
    return DeleteResult(ok=ok)

@router.post("/classes", response_model=ClassesConfig)
def set_global_classes(cfg: ClassesConfig):
    camera_service.set_global_classes(cfg.detect_classes)
    return cfg

@router.get("/classes", response_model=ClassesConfig)
def get_global_classes():
    v = camera_service.get_global_classes()
    return ClassesConfig(detect_classes=v or "all")

def mjpeg_generator(cam: dict) -> Iterator[bytes]:
    w = stream_service.ensure_worker(cam)
    boundary = b"--frame"
    while True:
        # ถ้า stream ถูกหยุด
        if not w.running:
            print(f"Stream {cam['id']} stopped. Exiting generator.")
            break

        frame = w.get_latest()
        if frame is None:
            time.sleep(0.05)
            continue

        jpg_bytes, _dets = detection_service.process(cam, frame)
        if not jpg_bytes:
            continue

        yield boundary + b"\r\n" + b"Content-Type: image/jpeg\r\n\r\n" + jpg_bytes + b"\r\n"

    print(f"Stream {cam['id']} generator closed cleanly.")


@router.get("/stream/{cam_id}")
def stream_mjpeg(cam_id: str):
    cam = camera_service.get(cam_id)
    if not cam:
        return JSONResponse({"detail": "camera not found"}, status_code=404)
    return StreamingResponse(mjpeg_generator(cam), media_type="multipart/x-mixed-replace; boundary=frame")

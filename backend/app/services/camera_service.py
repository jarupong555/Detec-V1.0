
import json, uuid
from typing import Dict, List
from ..core.config import CAMERAS_JSON
from ..core.logger import get_logger

log = get_logger("camera_service")

class CameraService:
    def __init__(self, base_stream_path: str = "/api/stream/"):
        self.base_stream_path = base_stream_path
        self._load()

    def _load(self):
        if CAMERAS_JSON.exists():
            self.cameras: Dict[str, dict] = json.loads(CAMERAS_JSON.read_text(encoding="utf-8"))
        else:
            self.cameras = {}
            self._save()

    def _save(self):
        CAMERAS_JSON.write_text(json.dumps(self.cameras, ensure_ascii=False, indent=2), encoding="utf-8")

    def list(self) -> List[dict]:
        return list(self.cameras.values())

    def add(self, name: str, location: str | None, protocol: str, source: str, detect_classes: str | None) -> dict:
        cam_id = uuid.uuid4().hex[:8]
        item = {
            "id": cam_id,
            "name": name,
            "location": location,
            "protocol": protocol,
            "source": source,
            "detect_classes": detect_classes,
            "stream_url": f"{self.base_stream_path}{cam_id}"
        }
        self.cameras[cam_id] = item
        self._save()
        log.info(f"Added camera {item}")
        return item

    def delete(self, cam_id: str) -> bool:
        if cam_id in self.cameras:
            del self.cameras[cam_id]
            self._save()
            return True
        return False

    def get(self, cam_id: str) -> dict | None:
        return self.cameras.get(cam_id)

    def set_global_classes(self, detect_classes: str):
        self.cameras["_global_classes"] = {"detect_classes": detect_classes}
        self._save()

    def get_global_classes(self) -> str | None:
        return self.cameras.get("_global_classes", {}).get("detect_classes")

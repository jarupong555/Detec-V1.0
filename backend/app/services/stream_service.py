import threading, time
import cv2
from typing import Dict, Optional
from ..infrastructure.camera_adapter import open_capture
from ..core.logger import get_logger

log = get_logger("stream_service")

class StreamWorker:
    def __init__(self, cam: dict):
        self.cam = cam
        self.cap = None
        self.frame = None
        self.lock = threading.Lock()
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def start(self):
        if self.running:
            return
        self.cap = open_capture(self.cam["protocol"], self.cam["source"])
        if self.cap is None:
            raise RuntimeError("Cannot open capture")
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        log.info(f"Started worker for {self.cam['id']}")

    def _loop(self):
        while self.running:
            if self.cap is None:
                break
            try:
                ok, frame = self.cap.read()
                if not ok:
                    if not self.running:
                        break
                    log.warning(f"Read fail {self.cam['id']}, retry in 1s")
                    time.sleep(1)
                    continue
                with self.lock:
                    self.frame = frame
            except cv2.error as e:
                log.warning(f"OpenCV read error for {self.cam['id']}: {e}")
                break
            except Exception as e:
                log.warning(f"Unknown error while reading {self.cam['id']}: {e}")
                break
            time.sleep(0.01)

        # cleanup หลังออกจาก loop
        if self.cap:
            try:
                self.cap.release()
            except Exception as e:
                log.warning(f"Error releasing capture {self.cam['id']}: {e}")
        self.cap = None
        log.info(f"Stopped worker loop for {self.cam['id']}")

    def get_latest(self):
        with self.lock:
            return None if self.frame is None else self.frame.copy()

    def stop(self):
        if not self.running:
            return
        log.info(f"Stopping worker for {self.cam['id']}")
        self.running = False
        try:
            if self.cap:
                self.cap.release()
                self.cap = None
        except Exception as e:
            log.warning(f"Error closing cap for {self.cam['id']}: {e}")
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3)
        log.info(f"Worker for {self.cam['id']} stopped cleanly")


class StreamService:
    def __init__(self):
        self.workers: Dict[str, StreamWorker] = {}

    def ensure_worker(self, cam: dict) -> StreamWorker:
        w = self.workers.get(cam["id"])
        if w is None:
            w = StreamWorker(cam)
            self.workers[cam["id"]] = w
            w.start()
        return w

    def stop_worker(self, cam_id: str):
        w = self.workers.pop(cam_id, None)
        if w:
            w.stop()
            log.info(f"Removed worker {cam_id} from registry")

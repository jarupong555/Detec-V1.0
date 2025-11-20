import cv2
import time
import threading
from queue import Queue
from typing import Optional
from ..core.logger import get_logger

log = get_logger("camera_adapter")

class SmoothBufferedCamera:
    def __init__(self, source: str, buffer_seconds: int = 5, target_fps: int = 25):
        self.source = source
        self.cap = self._open_capture(source)
        self.buffer = Queue(maxsize=buffer_seconds * target_fps)
        self.running = True
        self.fps = target_fps
        self.thread = threading.Thread(target=self._reader, daemon=True)
        self.thread.start()
        log.info(f"🎥 Buffered camera initialized (delay ~{buffer_seconds}s, {target_fps} FPS)")

    def _open_capture(self, source: str):
        """พยายามเปิดกล้องด้วย backend ปกติ ถ้าไม่ได้ fallback ไป CAP_FFMPEG"""
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            log.warning(f"Default backend failed for {source}, retrying with FFMPEG...")
            cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open source: {source}")
        return cap

    def _reader(self):
        while self.running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.05)
                    continue
                if self.buffer.full():
                    try:
                        self.buffer.get_nowait()
                    except:
                        pass
                self.buffer.put(frame)
            except Exception as e:
                log.warning(f"Camera reader error: {e}")
                break
        log.info("Reader thread stopped cleanly")

    def read(self):
        if not self.running:
            return False, None
        try:
            frame = self.buffer.get(timeout=1)
            time.sleep(1 / self.fps)
            return True, frame
        except:
            return False, None

    def release(self):
        self.running = False
        try:
            if self.cap:
                self.cap.release()
        except Exception as e:
            log.warning(f"Error releasing cap: {e}")
        with self.buffer.mutex:
            self.buffer.queue.clear()
        log.info("Buffered capture released")

def open_capture(protocol: str, source: str) -> Optional[SmoothBufferedCamera]:
    """
    เปิดกล้องหรือ stream พร้อม buffer ล่วงหน้า (เฉพาะ URL)
    """
    try:
        if protocol in ["rtsp", "http", "https", "rtmp", "hls"]:
            cam = SmoothBufferedCamera(source, buffer_seconds=8, target_fps=25)
            log.info("Pre-buffering network stream (wait ~8s)...")
            time.sleep(8)
            log.info("Stream ready and smooth playback enabled")
            return cam
        elif protocol == "usb":
            idx = int(source) if source.isdigit() else source
            cap = cv2.VideoCapture(idx)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
            return cap
        else:
            return SmoothBufferedCamera(source, buffer_seconds=5, target_fps=25)
    except Exception as e:
        log.error(f"Error opening camera: {e}")
        return None

import os
import time
import cv2
import requests
from dotenv import load_dotenv
from datetime import datetime
import pytz

from app.infrastructure.yolo_model import YoloDetector
from app.core.logger import get_logger

# ======================
# Load ENV
# ======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(os.path.dirname(BASE_DIR), ".env")
load_dotenv(ENV_PATH)

log = get_logger("headless")

# ======================
# ENV CONFIG
# ======================
CAMERA_LIST = os.getenv("CAMERA_LIST", "")
NOTIFY_URL = os.getenv("NOTIFY_URL", "")
DETECT_CLASSES = os.getenv("DETECT_CLASSES", "person,car").split(",")

DETECT_INTERVAL = 5  # save every 5 seconds

TH_TZ = pytz.timezone("Asia/Bangkok")
UTC_TZ = pytz.utc


# ======================
# Parse camera env
# ======================
def parse_camera_env():
    cams = []
    if not CAMERA_LIST.strip():
        return cams

    for entry in CAMERA_LIST.split(";"):
        entry = entry.strip()
        if not entry:
            continue

        parts = [p.strip() for p in entry.split(",")]
        if len(parts) < 4:
            log.warning(f"Invalid camera entry: {entry}")
            continue

        name, location, protocol, source = parts[:4]

        cams.append({
            "name": name,
            "location": location,
            "protocol": protocol.upper(),
            "source": source,
            "detect_classes": DETECT_CLASSES
        })

    return cams


# ======================
# Convert detection names → class id
# ======================
def get_class_ids(detector, target_classes):
    target_classes = [c.strip().lower() for c in target_classes]
    class_ids = []

    for cid, name in detector.names.items():
        if name.lower() in target_classes:
            class_ids.append(cid)

    return class_ids


# ======================
# Convert protocol → opencv source
# ======================
def get_video_source(cam):
    protocol = cam["protocol"]
    src = cam["source"]

    if protocol in ["USB", "WEBCAM"]:
        try:
            return int(src)
        except:
            log.error(f"USB/Webcam source ต้องเป็นตัวเลข เช่น 0, 1 → {src}")
            return None

    # RTSP / RTMP / HTTP / HLS ใช้ URL ได้เลย
    return src


# ======================
# Save annotated frame
# ======================
def save_image(cam, detections, frame):
    folder = f"captures/{cam['location']}/"
    os.makedirs(folder, exist_ok=True)

    cls_id, cls_name, conf, box, track_id = detections[0]

    now_th = datetime.now(TH_TZ)
    date_str = now_th.strftime("%Y%m%d")
    time_str = now_th.strftime("%H%M%S")

    filename = f"{cam['name']}_{cls_name}_{date_str}_{time_str}.jpg"
    filepath = os.path.join(folder, filename)

    cv2.imwrite(filepath, frame)
    log.info(f"Saved: {filepath}")

    utc_time = datetime.utcnow().replace(tzinfo=UTC_TZ)

    return filepath, filename, now_th, utc_time


# ======================
# Main processing loop
# ======================
if __name__ == "__main__":
    cams = parse_camera_env()
    if not cams:
        log.error("No cameras configured.")
        exit()

    detector = YoloDetector()

    active_cams = []
    for cam in cams:
        src = get_video_source(cam)
        if src is None:
            continue

        cap = cv2.VideoCapture(src)
        if not cap.isOpened():
            log.error(f"Cannot open camera: {cam['name']} source={src}")
            continue

        cam["cap"] = cap
        cam["class_ids"] = get_class_ids(detector, cam["detect_classes"])
        cam["last_save"] = 0

        active_cams.append(cam)
        log.info(f"Camera started: {cam['name']} ({cam['protocol']})")

    if not active_cams:
        log.error("No working cameras.")
        exit()

    log.info("Headless detection running...")

    while True:
        for cam in active_cams:
            ret, frame = cam["cap"].read()
            if not ret:
                log.warning(f"No frame: {cam['name']}")
                continue

            annotated, detections = detector.detect(frame, cam["class_ids"])

            if len(detections) == 0:
                continue

            now = time.time()
            if now - cam["last_save"] < DETECT_INTERVAL:
                continue

            filepath, filename, th_time, utc_time = save_image(cam, detections, annotated)

            cam["last_save"] = now

            # JSON payload
            payload = {
                "camera": cam["name"],
                "location": cam["location"],
                "filename": filename,
                "thai_time": th_time.strftime("%Y-%m-%d %H:%M:%S"),
                "utc_time": utc_time.strftime("%Y-%m-%d %H:%M:%S")
            }

            print("\n======= JSON SENT TO API =======")
            print(payload)
            print("================================\n")

            try:
                res = requests.post(NOTIFY_URL, json=payload, timeout=10)
                log.info(f"API: {res.status_code}")
            except Exception as e:
                log.error(f"API ERROR: {e}")

        time.sleep(0.01)

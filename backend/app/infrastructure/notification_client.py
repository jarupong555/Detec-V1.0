
import requests
from datetime import datetime, timezone
import pytz
from ..core.config import NOTIFY_URL, TZ
from ..core.logger import get_logger

log = get_logger("notify")

def notify_saved(frame_name: str, dt_utc: datetime):
    if not NOTIFY_URL:
        log.info("NOTIFY_URL not set; skip notify.")
        return
    tz = pytz.timezone(TZ)
    payload = {
        "frame_name": frame_name,
        "time_utc": dt_utc.replace(tzinfo=timezone.utc).isoformat(),
        "time_th": dt_utc.astimezone(tz).isoformat()
    }
    try:
        r = requests.post(NOTIFY_URL, json=payload, timeout=5)
        log.info(f"Notify -> {r.status_code}: {payload}")
    except Exception as e:
        log.warning(f"Notify failed: {e}")

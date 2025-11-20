
from pydantic import BaseModel, Field
from typing import Optional, Literal

Protocol = Literal["usb", "rtsp", "rtmp", "http", "hls"]

class CameraIn(BaseModel):
    name: str = Field(..., description="ชื่อกล้อง")
    location: Optional[str] = Field(None, description="โลเคชัน/โซน")
    protocol: Protocol
    source: str = Field(..., description="ลิ้ง/พาธวิดีโอ เช่น rtsp://..., /dev/video0 หรือ 0")
    detect_classes: Optional[str] = Field(None, description="คอมม่าคั่น หรือ 'all' (ว่าง=ใช้ค่ากลางจาก .env)")

class CameraOut(CameraIn):
    id: str
    stream_url: str

class ClassesConfig(BaseModel):
    detect_classes: str

class DeleteResult(BaseModel):
    ok: bool

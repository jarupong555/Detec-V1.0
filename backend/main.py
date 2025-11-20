from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.detection_routes import router as detection_router
from app.api.websocket_routes import router as ws_router
import uvicorn
import traceback
import sys

app = FastAPI(title="Face Detect Clean - YOLOv8")

# CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# router
app.include_router(detection_router, prefix="/api", tags=["detection"])
app.include_router(ws_router, prefix="/ws", tags=["websocket"])


@app.get("/")
def root():
    return {"ok": True, "name": "face-detect-clean", "status": "running"}


# main.py
if __name__ == "__main__":
    try:
        print("Starting Face Detect Backend...")
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    except KeyboardInterrupt:
        print("Server stopped cleanly. Bye bye!")
    except Exception as e:
        print("Server crashed unexpectedly!")
        traceback.print_exc()
        sys.exit(1)

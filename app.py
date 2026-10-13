"""
FlowMorph Studio - Application Gateway
Supports both the new Desktop Python GUI and the legacy headless/web API server.
"""

import sys
import os
import ctypes
import tempfile

if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
from typing import Optional, Callable
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Import the core engine (identical mathematical implementation)
from core.interpolator import OpticalFlowFrameInterpolator

progress_db = {}

# FastAPI Application instance for web/API integration
app = FastAPI(
    title="FlowMorph Studio API",
    description="Dense Optical Flow Video Frame Rate Upsampler",
    version="2.0.0",
)


@app.post("/process")
def process_video_endpoint(
    file: UploadFile = File(...),
    fps: float = Form(60.0),
    preset: str = Form("medium"),
    consistency_threshold: float = Form(0.15),
    task_id: str = Form(...),
):
    preset_lookup = {
        "ultrafast": cv2.DISOPTICAL_FLOW_PRESET_ULTRAFAST,
        "fast": cv2.DISOPTICAL_FLOW_PRESET_FAST,
        "medium": cv2.DISOPTICAL_FLOW_PRESET_MEDIUM,
    }

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as in_temp:
        in_temp.write(file.file.read())
        input_path = in_temp.name

    output_path = input_path.replace(".mp4", "_out.mp4")

    interpolator = OpticalFlowFrameInterpolator(
        target_fps=fps,
        flow_preset=preset_lookup.get(preset, cv2.DISOPTICAL_FLOW_PRESET_MEDIUM),
        consistency_threshold=consistency_threshold,
    )

    def update_progress(p: int):
        progress_db[task_id] = p

    interpolator.process_video(input_path, output_path, cb=update_progress)

    return FileResponse(output_path, media_type="video/mp4", filename="interpolated.mp4")


@app.get("/progress/{task_id}")
def get_progress(task_id: str):
    return {"progress": progress_db.get(task_id, 0)}


# Mount static directory if it exists for backward compatibility
if os.path.isdir("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        import uvicorn
        uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
    else:
        # Launch modern Python GUI by default
        from gui import FlowMorphApp

        gui = FlowMorphApp()
        gui.mainloop()
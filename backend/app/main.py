from typing import Annotated

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import AnalysisOut
from app.vision.pipeline import VisionPipeline

app = FastAPI(title="Detector de movimiento", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

pipeline = VisionPipeline()
MAX_IMAGE_BYTES = 2_000_000
MAX_IMAGE_DIMENSION = 800


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze", response_model=AnalysisOut)
async def analyze_frame(
    file: Annotated[UploadFile, File(description="JPEG frame captured by the browser")],
    session_id: Annotated[str, Form(min_length=1, max_length=100)],
    sensitivity: Annotated[int, Form(ge=0, le=100)] = 50,
) -> AnalysisOut:
    content = await file.read(MAX_IMAGE_BYTES + 1)
    if not content or len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="La imagen está vacía o supera 2 MB.")

    image = cv2.imdecode(np.frombuffer(content, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="El archivo recibido no es una imagen válida.")

    height, width = image.shape[:2]
    if max(height, width) > MAX_IMAGE_DIMENSION:
        scale = MAX_IMAGE_DIMENSION / max(height, width)
        image = cv2.resize(
            image,
            (round(width * scale), round(height * scale)),
            interpolation=cv2.INTER_AREA,
        )

    return pipeline.analyze(session_id, image, sensitivity)


@app.delete("/api/sessions/{session_id}", status_code=204)
def reset_session(session_id: str) -> None:
    pipeline.reset(session_id)

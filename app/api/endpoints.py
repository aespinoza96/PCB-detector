from fastapi import APIRouter, UploadFile, File, HTTPException, Response, Depends
from fastapi.responses import JSONResponse
from app.core.dependencies import get_detector, get_settings
from app.services.detection import DetectionService
from app.utils.image import validate_file, draw_detections, pil_image_to_bytes
from typing import Any
import os

router = APIRouter()

@router.get("/health")
def health(settings = Depends(get_settings)):
    return {"status": "healthy", "model_path": settings.MODEL_PATH}

@router.get("/")
def root(settings = Depends(get_settings)):
    return {
        "message": settings.TITLE,
        "version": settings.API_VERSION,
        "description": settings.DESCRIPTION
    }

@router.post("/predict")
async def predict(
    file: UploadFile = File(...),
    detector = Depends(get_detector),
    settings = Depends(get_settings)
):
    filename = file.filename or "image.jpg"
    content_type = file.content_type or "image/jpeg"
    if not validate_file(filename, content_type, settings.ALLOWED_EXTENSIONS, settings.ALLOWED_MIME_TYPES):
        raise HTTPException(status_code=400, detail="Invalid file type or extension.")
    service = DetectionService(detector)
    detections, tmp_path, _ = service.detect(file, settings.ALLOWED_EXTENSIONS, settings.ALLOWED_MIME_TYPES)
    if detections is None or tmp_path is None:
        raise HTTPException(status_code=400, detail="Could not process image.")
    os.remove(tmp_path)
    return JSONResponse(content={"detections": detections})

@router.post("/predict-image")
async def predict_image(
    file: UploadFile = File(...),
    detector = Depends(get_detector),
    settings = Depends(get_settings)
):
    filename = file.filename or "image.jpg"
    content_type = file.content_type or "image/jpeg"
    if not validate_file(filename, content_type, settings.ALLOWED_EXTENSIONS, settings.ALLOWED_MIME_TYPES):
        raise HTTPException(status_code=400, detail="Invalid file type or extension.")
    service = DetectionService(detector)
    detections, tmp_path, pil_image = service.detect(file, settings.ALLOWED_EXTENSIONS, settings.ALLOWED_MIME_TYPES)
    if detections is None or tmp_path is None or pil_image is None:
        raise HTTPException(status_code=400, detail="Could not process image.")
    annotated_image = draw_detections(pil_image, detections)
    img_bytes = pil_image_to_bytes(annotated_image)
    os.remove(tmp_path)
    return Response(content=img_bytes, media_type="image/png") 
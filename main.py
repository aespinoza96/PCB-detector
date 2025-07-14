from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from ultralytics import YOLO
import cv2
import numpy as np
import tempfile
import shutil
import os
import io
import logging
import asyncio
from typing import Optional, List, Dict, Any
from PIL import Image, ImageDraw, ImageFont
import time
from functools import lru_cache
import hashlib
from pathlib import Path
import mimetypes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer(auto_error=False)

# Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/bmp', 'image/tiff'}
CACHE_SIZE = 100

app = FastAPI(
    title="PCB Detector API",
    description="AI-powered PCB component detection service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
model: Optional[YOLO] = None
request_count = 0
start_time = time.time()

def load_model():
    """Load the YOLO model with error handling"""
    global model
    try:
        model_path = Path("best.pt")
        if not model_path.exists():
            raise FileNotFoundError(f"Model file {model_path} not found")
        
        model = YOLO(str(model_path))
        logger.info("Model loaded successfully")
        return model
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def validate_file(file: UploadFile) -> None:
    """Validate uploaded file"""
    # Check file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Max size: {MAX_FILE_SIZE} bytes")
    
    # Check file extension
    if file.filename:
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Invalid file extension. Allowed: {ALLOWED_EXTENSIONS}")
    
    # Check MIME type
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {ALLOWED_MIME_TYPES}")

@lru_cache(maxsize=CACHE_SIZE)
def get_font():
    """Get font with caching"""
    try:
        return ImageFont.truetype("arial.ttf", 16)
    except:
        return ImageFont.load_default()

def calculate_image_hash(image_array: np.ndarray) -> str:
    """Calculate hash for image caching"""
    return hashlib.md5(image_array.tobytes()).hexdigest()

async def run_inference_async(image_path: str) -> Any:
    """Run YOLO inference in thread pool to avoid blocking"""
    if model is None:
        raise RuntimeError("Model not loaded")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, model, image_path)

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    global model
    logger.info("Starting PCB Detector API...")
    model = load_model()
    logger.info("Application startup complete")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global request_count, start_time
    uptime = time.time() - start_time
    
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "uptime_seconds": uptime,
        "total_requests": request_count
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "PCB Detector API",
        "version": "1.0.0",
        "endpoints": {
            "/predict": "Get detections in JSON format",
            "/predict-image": "Get annotated image with detections",
            "/health": "Health check"
        }
    }

@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    token: Optional[str] = Depends(security)
):
    """Get detections in JSON format"""
    global request_count
    request_count += 1
    
    start_time = time.time()
    logger.info(f"Processing prediction request for file: {file.filename}")
    
    try:
        # Validate file
        validate_file(file)
        
        # Process image
        detections, tmp_path, _ = await process_image(file)
        
        if detections is None or tmp_path is None:
            raise HTTPException(status_code=400, detail="Could not process image")
        
        # Clean up
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        
        processing_time = time.time() - start_time
        logger.info(f"Prediction completed in {processing_time:.2f}s")
        
        return JSONResponse(content={
            "detections": detections,
            "processing_time": processing_time,
            "image_size": file.size
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in prediction: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/predict-image")
async def predict_image(
    file: UploadFile = File(...),
    token: Optional[str] = Depends(security)
):
    """Get annotated image with detections"""
    global request_count
    request_count += 1
    
    start_time = time.time()
    logger.info(f"Processing image prediction request for file: {file.filename}")
    
    try:
        # Validate file
        validate_file(file)
        
        # Process image
        detections, tmp_path, pil_image = await process_image(file)
        
        if detections is None or tmp_path is None or pil_image is None:
            raise HTTPException(status_code=400, detail="Could not process image")
        
        # Draw annotations
        annotated_image = draw_detections(pil_image, detections)
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        annotated_image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        # Clean up
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        
        processing_time = time.time() - start_time
        logger.info(f"Image prediction completed in {processing_time:.2f}s")
        
        return Response(
            content=img_byte_arr.getvalue(), 
            media_type="image/png",
            headers={"X-Processing-Time": str(processing_time)}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in image prediction: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

def draw_detections(pil_image: Image.Image, detections: List[Dict]) -> Image.Image:
    """Draw detection annotations on image"""
    draw = ImageDraw.Draw(pil_image)
    font = get_font()
    
    for detection in detections:
        bbox = detection["bbox"]
        conf = detection["confidence"]
        class_name = detection["class_name"]
        
        # Convert coordinates to integers
        x1, y1, x2, y2 = map(int, bbox)
        
        # Draw bounding box
        draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
        
        # Draw label with confidence
        label = f"{class_name}: {conf:.2f}"
        label_bbox = draw.textbbox((x1, y1-20), label, font=font)
        draw.rectangle(label_bbox, fill="red")
        draw.text((x1, y1-20), label, fill="white", font=font)
    
    return pil_image

async def process_image(file: UploadFile):
    """
    Process uploaded image and get detections.
    Returns tuple of (detections, image_path, pil_image) or (None, None, None) on error.
    """
    filename = file.filename or "image.jpg"
    suffix = os.path.splitext(filename)[-1] or ".png"
    
    # Validate suffix
    if suffix.lower() not in ALLOWED_EXTENSIONS:
        logger.warning(f"Invalid file extension: {suffix}")
        return None, None, None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        # Load the image
        image = cv2.imread(tmp_path)
        if image is None:
            logger.error(f"Failed to load image: {tmp_path}")
            os.remove(tmp_path)
            return None, None, None
        
        # Convert BGR to RGB for PIL
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)

        # Run inference asynchronously
        results = await run_inference_async(tmp_path)
        results = results[0]  # Get first result

        detections = []
        for box in results.boxes:
            bbox = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            if model is None:
                raise RuntimeError("Model not loaded")
            detections.append({
                "bbox": bbox,
                "confidence": conf,
                "class_id": cls,
                "class_name": model.names[cls]
            })

        return detections, tmp_path, pil_image
        
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        # Clean up temp file if it exists
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
        return None, None, None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
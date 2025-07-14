import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import cv2
import io
import logging
from typing import List, Dict, Any, Set, Optional

logger = logging.getLogger(__name__)

def validate_file(filename: str, content_type: str, allowed_exts: Set[str], allowed_mimes: Set[str]) -> bool:
    ext = Path(filename).suffix.lower()
    if ext not in allowed_exts:
        logger.warning(f"Invalid file extension: {ext}")
        return False
    if content_type not in allowed_mimes:
        logger.warning(f"Invalid MIME type: {content_type}")
        return False
    return True

def load_image_to_pil(tmp_path: str) -> Optional[Image.Image]:
    image = cv2.imread(tmp_path)
    if image is None:
        logger.error(f"Failed to load image: {tmp_path}")
        return None
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return Image.fromarray(image_rgb)

def draw_detections(pil_image: Image.Image, detections: List[Dict[str, Any]], font_path: str = "arial.ttf", font_size: int = 16) -> Image.Image:
    draw = ImageDraw.Draw(pil_image)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()
    for detection in detections:
        bbox = detection["bbox"]
        conf = detection["confidence"]
        class_name = detection["class_name"]
        x1, y1, x2, y2 = map(int, bbox)
        draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
        label = f"{class_name}: {conf:.2f}"
        label_bbox = draw.textbbox((x1, y1-20), label, font=font)
        draw.rectangle(label_bbox, fill="red")
        draw.text((x1, y1-20), label, fill="white", font=font)
    return pil_image

def pil_image_to_bytes(pil_image: Image.Image) -> bytes:
    img_byte_arr = io.BytesIO()
    pil_image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue() 
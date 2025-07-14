from app.models.base import BaseDetector
from app.utils.image import load_image_to_pil
from typing import List, Dict, Any, Optional, Tuple
import tempfile
import shutil
import os
import logging

logger = logging.getLogger(__name__)

class DetectionService:
    def __init__(self, detector: BaseDetector):
        self.detector = detector

    def detect(self, file, allowed_exts, allowed_mimes) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str], Optional[Any]]:
        filename = file.filename or "image.jpg"
        suffix = os.path.splitext(filename)[-1] or ".png"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        pil_image = load_image_to_pil(tmp_path)
        if pil_image is None:
            os.remove(tmp_path)
            return None, None, None
        detections = self.detector.predict(tmp_path)
        return detections, tmp_path, pil_image 
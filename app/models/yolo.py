from ultralytics import YOLO
from app.models.base import BaseDetector
from typing import Any, List, Dict
import logging

class YOLODetector(BaseDetector):
    def __init__(self, model_path: str):
        self.logger = logging.getLogger(__name__)
        try:
            self.model = YOLO(model_path)
            self.names = self.model.names
            self.logger.info(f"YOLO model loaded from {model_path}")
        except Exception as e:
            self.logger.error(f"Failed to load YOLO model: {e}")
            raise

    def predict(self, image_path: str) -> List[Dict[str, Any]]:
        results = self.model(image_path)[0]
        detections = []
        for box in results.boxes:
            bbox = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            detections.append({
                "bbox": bbox,
                "confidence": conf,
                "class_id": cls,
                "class_name": self.names[cls]
            })
        return detections 
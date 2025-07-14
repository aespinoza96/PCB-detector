from app.core.config import settings
from app.models.yolo import YOLODetector
from functools import lru_cache

@lru_cache(maxsize=1)
def get_settings():
    return settings

@lru_cache(maxsize=1)
def get_detector():
    return YOLODetector(settings.MODEL_PATH) 
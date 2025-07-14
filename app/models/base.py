from abc import ABC, abstractmethod
from typing import Any, List, Dict

class BaseDetector(ABC):
    @abstractmethod
    def predict(self, image_path: str) -> List[Dict[str, Any]]:
        """Run detection on the given image path and return a list of detections."""
        pass 
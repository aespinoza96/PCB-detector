from pydantic import BaseSettings
from typing import Set

class Settings(BaseSettings):
    MODEL_PATH: str = "best.pt"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: Set[str] = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    ALLOWED_MIME_TYPES: Set[str] = {'image/jpeg', 'image/png', 'image/bmp', 'image/tiff'}
    CORS_ORIGINS: list[str] = ["*"]
    LOG_LEVEL: str = "INFO"
    API_VERSION: str = "1.0.0"
    TITLE: str = "PCB Detector API"
    DESCRIPTION: str = "Servicio de detección de errores en PCB"
    
    class Config:
        env_file = ".env"

settings = Settings() 
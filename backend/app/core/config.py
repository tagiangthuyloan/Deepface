import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "DeepFace-System"
    
    # Qdrant (Vector DB)
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "qdrant")
    QDRANT_PORT: int = 6333
    COLLECTION_NAME: str = "employees"
    
    # Redis (Message Queue)
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

    # DeepFace
    FACE_MODEL: str = "ArcFace" 

settings = Settings()
"""
Configuration settings for Local AI-BI Platform
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional, Union
import os
import json


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = "postgresql://aibi_user:local_password@postgres:5432/aibi"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # MinIO (Local S3-compatible storage)
    MINIO_URL: str = "http://minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET: str = "aibi-data"
    
    # Ollama (Local LLM)
    OLLAMA_URL: str = "http://ollama:11434"
    OLLAMA_MODEL_CHAT: str = "llama2:7b-chat"
    OLLAMA_MODEL_CODE: str = "codellama:7b"
    
    # File upload settings
    UPLOAD_DIR: str = "/app/uploads"
    PROCESSED_DIR: str = "/app/processed"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_FILE_TYPES: List[str] = [
        "text/csv",
        "text/tsv",
        "text/tab-separated-values",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/json",
        "application/parquet",
        "application/xml",
        "text/xml"
    ]
    
    # Data source types
    SUPPORTED_DATA_SOURCES: List[str] = [
        "file",
        "database", 
        "api",
        "hdfs"
    ]
    
    # CORS settings
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            if not v.strip():
                # Empty string, use default
                return ["http://localhost:3000", "http://127.0.0.1:3000"]
            try:
                # Try to parse as JSON
                return json.loads(v)
            except json.JSONDecodeError:
                # Treat as comma-separated URLs
                origins = [url.strip() for url in v.split(',') if url.strip()]
                return origins if origins else ["http://localhost:3000", "http://127.0.0.1:3000"]
        return v
    
    # Security
    SECRET_KEY: str = "local-ai-bi-secret-key-change-in-production"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"


# Create settings instance
settings = Settings()
"""
Production-ready configuration settings for the Mistral API server.
"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    
    # Model Configuration
    model_path: str = "/teamspace/studios/this_studio/Mentay-Complete-Model-v1/checkpoints/checkpoint_000100/consolidated"
    max_tokens: int = 4096
    default_temperature: float = 0.7
    default_top_p: float = 1.0
    
    # Security
    cors_origins: List[str] = ["*"]
    api_keys: List[str] = ["sk-mistral-api-key"]  # Change in production
    
    # Performance
    max_concurrent_requests: int = 10
    request_timeout: int = 300
    
    # Logging
    log_level: str = "INFO"
    enable_metrics: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
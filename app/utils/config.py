# app/utils/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Optional
from pydantic import field_validator

class Settings(BaseSettings):
    # OpenAI Configuration
    openai_url: str = "http://host.docker.internal:11434/v1"
    openai_api_key: str = "ollama-key"
    openai_model: str = "gpt-4o-mini"
    
    # Presidio Configuration
    presidio_analyzer_url: str = "http://presidio-analyzer:3000"
    presidio_anonymizer_url: str = "http://presidio-anonymizer:3000"
    
    # Security Configuration
    api_key: Optional[str] = None
    enable_auth: bool = True
    allowed_origins: List[str] = ["*"]
    
    # Rate Limiting Configuration
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60
    rate_limit_redis_url: str = "redis://redis:6379/0"
    
    # Audit Logging Configuration
    audit_log_enabled: bool = True
    audit_log_file: str = "logs/audit.log"
    audit_log_max_file_size: int = 10 * 1024 * 1024  # 10MB
    audit_log_backup_count: int = 5
    
    # PDF Configuration
    pdf_max_file_size: int = 10 * 1024 * 1024  # 10MB
    pdf_ocr_enabled: bool = True
    pdf_ocr_language: str = "eng"
    pdf_ocr_dpi: int = 300
    
    # DOCX Configuration
    docx_max_file_size: int = 5 * 1024 * 1024  # 5MB
    
    # Image Configuration
    image_max_file_size: int = 10 * 1024 * 1024  # 10MB
    image_ocr_config: dict = {
        "psm": 6,
        "oem": 3,
        "lang": "eng",
        "enhance_contrast": True,
        "denoise": True,
        "threshold": True,
        "correct_rotation": True,
        "enhance_quality": True,
        "preserve_interword_spaces": True
    }
    
    # Text Configuration
    text_max_file_size: int = 1 * 1024 * 1024  # 1MB
    
    # Language Detection Configuration
    language_min_confidence: float = 0.8
    language_max_text_length: int = 10000
    
    # Custom Entities Configuration
    custom_entities_config_path: str = "config/custom_entities.yaml"
    
    # Environment
    environment: str = "development"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

# Alias for backward compatibility
get_config = get_settings

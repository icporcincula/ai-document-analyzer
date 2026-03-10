# app/utils/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Optional

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
    
    # Environment
    environment: str = "development"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

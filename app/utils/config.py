# app/utils/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    openai_url: str = "http://host.docker.internal:11434/v1"
    openai_api_key: str = "ollama-key"
    openai_model: str = "gpt-4o-mini"
    presidio_analyzer_url: str = "http://presidio-analyzer:3000"
    presidio_anonymizer_url: str = "http://presidio-anonymizer:3000"
    environment: str = "development"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
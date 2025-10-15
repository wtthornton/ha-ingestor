"""Configuration management for AI Automation Service"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment"""
    
    # Data API
    data_api_url: str = "http://data-api:8006"
    
    # Home Assistant
    ha_url: str
    ha_token: str
    
    # MQTT
    mqtt_broker: str
    mqtt_port: int = 1883
    mqtt_username: Optional[str] = None
    mqtt_password: Optional[str] = None
    
    # OpenAI
    openai_api_key: str
    
    # Scheduling
    analysis_schedule: str = "0 3 * * *"  # 3 AM daily (cron format)
    
    # Database
    database_path: str = "/app/data/ai_automation.db"
    database_url: str = "sqlite+aiosqlite:///data/ai_automation.db"
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = "infrastructure/env.ai-automation"
        case_sensitive = False


# Global settings instance
settings = Settings()


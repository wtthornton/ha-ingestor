"""Configuration management for AI Automation Service"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment"""
    
    # Data API
    data_api_url: str = "http://data-api:8006"
    
    # InfluxDB (for direct event queries)
    influxdb_url: str = "http://influxdb:8086"
    influxdb_token: str = "ha-ingestor-token"
    influxdb_org: str = "ha-ingestor"
    influxdb_bucket: str = "home_assistant_events"
    
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
    
    # Safety Validation (AI1.19)
    safety_level: str = "moderate"  # strict, moderate, or permissive
    safety_allow_override: bool = True  # Allow force_deploy override
    safety_min_score: int = 60  # Minimum safety score for moderate level
    
    # Natural Language Generation (AI1.21)
    nl_generation_enabled: bool = True
    nl_model: str = "gpt-4o-mini"  # OpenAI model for NL generation
    nl_max_tokens: int = 1500
    nl_temperature: float = 0.3  # Lower = more consistent
    
    class Config:
        env_file = "infrastructure/env.ai-automation"
        case_sensitive = False


# Global settings instance
settings = Settings()


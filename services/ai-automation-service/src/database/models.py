"""
SQLAlchemy database models for AI Automation Service

Epic AI-1: Pattern detection and automation suggestions
Epic AI-2: Device intelligence and capability tracking
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class Pattern(Base):
    """Detected automation patterns"""
    __tablename__ = 'patterns'
    
    id = Column(Integer, primary_key=True)
    pattern_type = Column(String, nullable=False)  # 'time_of_day', 'co_occurrence', 'anomaly'
    device_id = Column(String, nullable=False)
    pattern_metadata = Column(JSON)  # Pattern-specific data (renamed from 'metadata' to avoid SQLAlchemy reserved name)
    confidence = Column(Float, nullable=False)
    occurrences = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Pattern(id={self.id}, type={self.pattern_type}, device={self.device_id}, confidence={self.confidence})>"


class Suggestion(Base):
    """Automation suggestions generated from patterns"""
    __tablename__ = 'suggestions'
    
    id = Column(Integer, primary_key=True)
    pattern_id = Column(Integer, ForeignKey('patterns.id'), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    automation_yaml = Column(Text, nullable=False)
    status = Column(String, default='pending')  # pending, approved, deployed, rejected
    confidence = Column(Float, nullable=False)
    category = Column(String, nullable=True)  # energy, comfort, security, convenience
    priority = Column(String, nullable=True)  # high, medium, low
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deployed_at = Column(DateTime, nullable=True)
    ha_automation_id = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<Suggestion(id={self.id}, title={self.title}, status={self.status})>"


class UserFeedback(Base):
    """User feedback on suggestions"""
    __tablename__ = 'user_feedback'
    
    id = Column(Integer, primary_key=True)
    suggestion_id = Column(Integer, ForeignKey('suggestions.id'))
    action = Column(String, nullable=False)  # 'approved', 'rejected', 'modified'
    feedback_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserFeedback(id={self.id}, suggestion_id={self.suggestion_id}, action={self.action})>"


class AutomationVersion(Base):
    """
    Simple version history for automations.
    Keeps last 3 versions per automation for rollback.
    
    Story AI1.20: Simple Rollback
    """
    __tablename__ = 'automation_versions'
    
    id = Column(Integer, primary_key=True)
    automation_id = Column(String(100), nullable=False, index=True)
    yaml_content = Column(Text, nullable=False)
    deployed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    safety_score = Column(Integer, nullable=False)
    
    def __repr__(self):
        return f"<AutomationVersion(id={self.id}, automation_id={self.automation_id}, deployed_at={self.deployed_at})>"


# ============================================================================
# Epic AI-2: Device Intelligence Models (Story AI2.2)
# ============================================================================

class DeviceCapability(Base):
    """
    Device capability definitions from Zigbee2MQTT bridge.
    
    Stores universal capability data for device models. One record per
    unique model (e.g., "VZM31-SN", "MCCGQ11LM").
    
    Story AI2.2: Capability Database Schema & Storage
    Epic AI-2: Device Intelligence System
    
    Integration:
        Links to devices table via device.model field (cross-database)
        Devices are in data-api's metadata.db, capabilities in ai_automation.db
    
    Example:
        VZM31-SN -> {led_notifications, smart_bulb_mode, auto_off_timer, ...}
    """
    __tablename__ = 'device_capabilities'
    
    # Primary Key
    device_model = Column(String, primary_key=True)  # e.g., "VZM31-SN"
    
    # Device Identification
    manufacturer = Column(String, nullable=False)  # e.g., "Inovelli"
    integration_type = Column(String, nullable=False, default='zigbee2mqtt')
    description = Column(String, nullable=True)
    
    # Capability Data (JSON columns)
    capabilities = Column(JSON, nullable=False)  # Parsed, structured format
    mqtt_exposes = Column(JSON, nullable=True)   # Raw Zigbee2MQTT exposes (backup)
    
    # Metadata
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = Column(String, default='zigbee2mqtt_bridge')
    
    def __repr__(self):
        return f"<DeviceCapability(model='{self.device_model}', manufacturer='{self.manufacturer}', features={len(self.capabilities) if self.capabilities else 0})>"


class DeviceFeatureUsage(Base):
    """
    Track feature usage per device instance.
    
    Records which features are configured vs. available for each physical
    device. Used for utilization analysis and unused feature detection.
    
    Story AI2.2: Capability Database Schema & Storage
    Epic AI-2: Device Intelligence System
    
    Composite Primary Key: (device_id, feature_name)
    
    Integration:
        device_id links to devices.device_id in data-api's metadata.db (logical FK)
    
    Example:
        ("kitchen_switch", "led_notifications", configured=False)
        ("kitchen_switch", "smart_bulb_mode", configured=True)
    """
    __tablename__ = 'device_feature_usage'
    
    # Composite Primary Key
    device_id = Column(String, primary_key=True)       # FK to devices.device_id (cross-DB)
    feature_name = Column(String, primary_key=True)    # e.g., "led_notifications"
    
    # Usage Tracking
    configured = Column(Boolean, default=False, nullable=False)
    discovered_date = Column(DateTime, default=datetime.utcnow)
    last_checked = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<DeviceFeatureUsage(device='{self.device_id}', feature='{self.feature_name}', configured={self.configured})>"


# Indexes for fast lookups (Epic AI-2)
Index('idx_capabilities_manufacturer', DeviceCapability.manufacturer)
Index('idx_capabilities_integration', DeviceCapability.integration_type)
Index('idx_feature_usage_device', DeviceFeatureUsage.device_id)
Index('idx_feature_usage_configured', DeviceFeatureUsage.configured)


# Database engine and session
engine = None
async_session = None


async def init_db():
    """Initialize database - create tables if they don't exist"""
    global engine, async_session
    
    # Create async engine
    engine = create_async_engine(
        'sqlite+aiosqlite:///data/ai_automation.db',
        echo=False  # Set to True for SQL debugging
    )
    
    # Create session factory
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database initialized successfully")
    return engine, async_session


async def get_db():
    """Dependency for FastAPI routes to get database session"""
    async with async_session() as session:
        yield session


def get_db_session():
    """
    Get database session as async context manager.
    
    Usage:
        async with get_db_session() as db:
            result = await db.execute(query)
    """
    return async_session()

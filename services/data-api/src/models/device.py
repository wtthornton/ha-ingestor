"""
Device Model for SQLite Storage
Story 22.2 - Simple device registry
"""

from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class Device(Base):
    """Device registry model - stores HA device metadata"""
    
    __tablename__ = "devices"
    
    # Primary key
    device_id = Column(String, primary_key=True)
    
    # Device metadata
    name = Column(String, nullable=False)
    manufacturer = Column(String)
    model = Column(String)
    sw_version = Column(String)
    area_id = Column(String, index=True)  # Room/area location
    integration = Column(String, index=True)  # HA integration source
    
    # Timestamps
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to entities
    entities = relationship("Entity", back_populates="device", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Device(device_id='{self.device_id}', name='{self.name}')>"


# Indexes for common queries
Index('idx_device_area', Device.area_id)
Index('idx_device_integration', Device.integration)
Index('idx_device_manufacturer', Device.manufacturer)


"""
Entity Model for SQLite Storage
Story 22.2 - Simple entity registry with FK to devices
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class Entity(Base):
    """Entity registry model - stores HA entity metadata with device relationship"""
    
    __tablename__ = "entities"
    
    # Primary key
    entity_id = Column(String, primary_key=True)
    
    # Foreign key to device
    device_id = Column(String, ForeignKey("devices.device_id", ondelete="CASCADE"), index=True)
    
    # Entity metadata
    domain = Column(String, nullable=False, index=True)  # light, sensor, switch, etc.
    platform = Column(String)  # Integration platform
    unique_id = Column(String)  # Unique ID within platform
    area_id = Column(String, index=True)  # Room/area location
    disabled = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to device
    device = relationship("Device", back_populates="entities")
    
    def __repr__(self):
        return f"<Entity(entity_id='{self.entity_id}', domain='{self.domain}')>"


# Indexes for common queries
Index('idx_entity_device', Entity.device_id)
Index('idx_entity_domain', Entity.domain)
Index('idx_entity_area', Entity.area_id)


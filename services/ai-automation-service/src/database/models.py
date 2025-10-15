"""SQLAlchemy database models for AI Automation Service"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
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
    metadata = Column(JSON)  # Pattern-specific data
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


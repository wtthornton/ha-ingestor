"""
Simple Webhook Model for SQLite Storage
Story 22.3 - Minimal implementation, no Alembic needed
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, create_engine
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Webhook(Base):
    """Webhook subscription model - super simple"""
    
    __tablename__ = "webhooks"
    
    webhook_id = Column(String, primary_key=True)
    url = Column(String, nullable=False)
    events = Column(String, nullable=False)  # JSON string
    secret = Column(String, nullable=False)
    team = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Stats
    total_calls = Column(Integer, default=0)
    failed_calls = Column(Integer, default=0)
    last_success = Column(String)  # ISO timestamp
    last_failure = Column(String)  # ISO timestamp
    enabled = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<Webhook(id='{self.webhook_id}', url='{self.url}')>"


def init_webhook_db(db_path: str = "data/webhooks.db"):
    """Initialize simple SQLite database for webhooks"""
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    
    # Enable WAL mode
    with engine.connect() as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.commit()
    
    # Create tables
    Base.metadata.create_all(engine)
    
    return engine


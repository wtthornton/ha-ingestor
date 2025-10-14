"""
Tests for Webhook SQLite storage
Story 22.3 - Simple tests
"""

import pytest
import json
from src.webhook_manager import WebhookManager
from src.webhook_model import Webhook, init_webhook_db
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker


def test_webhook_model_creation():
    """Test creating webhook model"""
    engine = init_webhook_db("data/test_webhooks.db")
    SessionLocal = sessionmaker(bind=engine)
    
    with SessionLocal() as session:
        webhook = Webhook(
            webhook_id="test_123",
            url="http://example.com/hook",
            events=json.dumps(["game_started", "score_changed"]),
            secret="secret123456789012",
            team="sf"
        )
        session.add(webhook)
        session.commit()
        
        # Verify
        result = session.execute(select(Webhook).where(Webhook.webhook_id == "test_123"))
        saved = result.scalar_one()
        assert saved.url == "http://example.com/hook"
        assert saved.team == "sf"
        
        # Cleanup
        session.delete(saved)
        session.commit()


def test_webhook_manager_register():
    """Test webhook registration with SQLite"""
    manager = WebhookManager(db_path="data/test_webhooks2.db")
    
    webhook_id = manager.register(
        url="http://test.com/hook",
        events=["game_started"],
        secret="test_secret_12345",
        team="dal"
    )
    
    assert webhook_id is not None
    assert webhook_id in manager.webhooks
    assert manager.webhooks[webhook_id]['url'] == "http://test.com/hook"
    
    # Cleanup
    manager.unregister(webhook_id)


def test_webhook_manager_unregister():
    """Test webhook deletion"""
    manager = WebhookManager(db_path="data/test_webhooks3.db")
    
    webhook_id = manager.register(
        url="http://test.com/hook2",
        events=["score_changed"],
        secret="test_secret_67890"
    )
    
    # Delete
    result = manager.unregister(webhook_id)
    assert result is True
    assert webhook_id not in manager.webhooks
    
    # Try delete again
    result = manager.unregister(webhook_id)
    assert result is False


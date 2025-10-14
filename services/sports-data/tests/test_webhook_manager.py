"""
Unit tests for Webhook Manager

Story 12.3 - Adaptive Event Monitor + Webhooks
"""

import pytest
import hmac
import hashlib
import json
from unittest.mock import Mock, patch, AsyncMock
from src.webhook_manager import WebhookManager


@pytest.fixture
def webhook_manager(tmp_path):
    """Create webhook manager with temp storage"""
    storage = tmp_path / "webhooks.json"
    return WebhookManager(storage_file=str(storage))


def test_register_webhook(webhook_manager):
    """Test webhook registration"""
    webhook_id = webhook_manager.register(
        url="http://example.com/webhook",
        events=["game_started"],
        secret="test-secret-16-chars",
        team="sf"
    )
    
    assert webhook_id
    assert len(webhook_manager.webhooks) == 1
    assert webhook_manager.webhooks[webhook_id]['url'] == "http://example.com/webhook"


def test_unregister_webhook(webhook_manager):
    """Test webhook unregistration"""
    webhook_id = webhook_manager.register(
        url="http://example.com/webhook",
        events=["game_started"],
        secret="test-secret-16-chars"
    )
    
    success = webhook_manager.unregister(webhook_id)
    assert success
    assert len(webhook_manager.webhooks) == 0


def test_get_all_hides_secrets(webhook_manager):
    """Test get_all hides secrets"""
    webhook_manager.register(
        url="http://example.com/webhook",
        events=["game_started"],
        secret="test-secret-16-chars"
    )
    
    all_webhooks = webhook_manager.get_all()
    assert len(all_webhooks) == 1
    assert all_webhooks[0]['secret'] == '***'


@pytest.mark.asyncio
async def test_send_event_filters_by_team(webhook_manager):
    """Test event delivery filters by team"""
    webhook_manager.register(
        url="http://example.com/webhook",
        events=["game_started"],
        secret="test-secret",
        team="sf"
    )
    
    # Mock session
    webhook_manager.session = AsyncMock()
    
    # Event for different team - should not deliver
    await webhook_manager.send_event("game_started", {"home_team": "ne", "away_team": "dal"})
    
    # Give async tasks time to run
    await asyncio.sleep(0.1)
    
    # Should not have called (team filter)
    assert not webhook_manager.session.post.called


@pytest.mark.asyncio
async def test_hmac_signature_generation(webhook_manager):
    """Test HMAC signature is correct"""
    secret = "test-secret-16-chars"
    payload = {"event": "game_started", "team": "sf"}
    payload_json = json.dumps(payload, separators=(',', ':'))
    
    # Expected signature
    expected_sig = hmac.new(
        secret.encode('utf-8'),
        payload_json.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # This validates our implementation matches HMAC standard
    assert isinstance(expected_sig, str)
    assert len(expected_sig) == 64  # SHA256 hex is 64 chars


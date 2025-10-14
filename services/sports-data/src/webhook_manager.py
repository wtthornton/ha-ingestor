"""
Simple Webhook Manager with HMAC Signing

Manages webhook subscriptions and secure delivery.
Story 12.3 - Adaptive Event Monitor + Webhooks
Story 22.3 - SQLite storage (simple, no Alembic)
"""

import os
import json
import hmac
import hashlib
import asyncio
import logging
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, select, update, delete
from sqlalchemy.orm import sessionmaker

from .webhook_model import Webhook, init_webhook_db

logger = logging.getLogger(__name__)


class WebhookManager:
    """
    Simple webhook manager with HMAC-SHA256 signatures.
    
    Story 22.3: Now uses SQLite for concurrent-safe storage
    """
    
    def __init__(self, db_path: str = "data/webhooks.db"):
        """Initialize webhook manager with SQLite"""
        self.db_path = db_path
        self.webhooks: Dict[str, dict] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Initialize SQLite database
        Path("data").mkdir(exist_ok=True)
        self.engine = init_webhook_db(db_path)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Load from SQLite
        self._load_webhooks()
    
    async def startup(self):
        """Start aiohttp session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5)
        )
        logger.info("Webhook manager started")
    
    async def shutdown(self):
        """Cleanup"""
        if self.session:
            await self.session.close()
        # SQLite auto-saves, no manual save needed
        logger.info("Webhook manager stopped")
    
    def register(self, url: str, events: List[str], secret: str, team: Optional[str] = None) -> str:
        """Register webhook (SQLite)"""
        import uuid
        webhook_id = str(uuid.uuid4())
        
        # Insert into SQLite
        with self.SessionLocal() as session:
            webhook = Webhook(
                webhook_id=webhook_id,
                url=url,
                events=json.dumps(events),
                secret=secret,
                team=team
            )
            session.add(webhook)
            session.commit()
        
        # Update in-memory cache
        self.webhooks[webhook_id] = {
            'url': url,
            'events': events,
            'secret': secret,
            'team': team,
            'created_at': datetime.utcnow().isoformat(),
            'total_calls': 0,
            'failed_calls': 0,
            'last_success': None,
            'last_failure': None,
            'enabled': True
        }
        
        logger.info(f"Webhook registered: {webhook_id} -> {url}")
        return webhook_id
    
    def unregister(self, webhook_id: str) -> bool:
        """Remove webhook (SQLite)"""
        with self.SessionLocal() as session:
            result = session.execute(delete(Webhook).where(Webhook.webhook_id == webhook_id))
            session.commit()
            deleted = result.rowcount > 0
        
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
        
        if deleted:
            logger.info(f"Webhook unregistered: {webhook_id}")
        return deleted
    
    def get_all(self) -> List[dict]:
        """Get all webhooks (without secrets)"""
        return [
            {**config, 'secret': '***', 'id': wid}
            for wid, config in self.webhooks.items()
        ]
    
    async def send_event(self, event_type: str, event_data: dict):
        """
        Send event to matching webhooks (fire-and-forget).
        
        Args:
            event_type: Event type (game_started, score_changed, game_ended)
            event_data: Event payload
        """
        for webhook_id, config in self.webhooks.items():
            if not config['enabled']:
                continue
            
            if event_type not in config['events']:
                continue
            
            # Team filter
            if config['team']:
                if event_data.get('home_team') != config['team'] and event_data.get('away_team') != config['team']:
                    continue
            
            # Fire and forget
            asyncio.create_task(self._deliver(webhook_id, event_type, event_data))
    
    async def _deliver(self, webhook_id: str, event_type: str, event_data: dict):
        """
        Deliver webhook with HMAC signature and retry.
        
        Following Context7 KB best practices:
        - HMAC-SHA256 signature
        - Headers: X-Webhook-Signature, X-Webhook-Event, X-Webhook-Timestamp
        - 3 retries with exponential backoff (1s, 2s, 4s)
        """
        config = self.webhooks.get(webhook_id)
        if not config:
            return
        
        # Add metadata
        payload = {
            **event_data,
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Serialize
        payload_json = json.dumps(payload, separators=(',', ':'))
        payload_bytes = payload_json.encode('utf-8')
        
        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            config['secret'].encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        
        # Headers (following KB pattern)
        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Signature': signature,
            'X-Webhook-Event': event_type,
            'X-Webhook-Timestamp': payload['timestamp'],
            'X-Webhook-ID': webhook_id,
            'User-Agent': 'SportsDataService/2.0'
        }
        
        # Retry with exponential backoff
        for attempt in range(3):
            try:
                async with self.session.post(
                    config['url'],
                    data=payload_json,
                    headers=headers
                ) as response:
                    if response.status in (200, 201, 202):
                        config['total_calls'] += 1
                        config['last_success'] = datetime.utcnow().isoformat()
                        logger.info(f"Webhook delivered: {webhook_id} -> {event_type}")
                        return
                    else:
                        logger.warning(f"Webhook failed: {webhook_id} HTTP {response.status}")
            
            except Exception as e:
                logger.error(f"Webhook error: {webhook_id} - {e}")
            
            # Exponential backoff: 1s, 2s, 4s
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
        
        # All failed - update stats in SQLite
        config['failed_calls'] += 1
        config['last_failure'] = datetime.utcnow().isoformat()
        
        try:
            with self.SessionLocal() as session:
                session.execute(
                    update(Webhook)
                    .where(Webhook.webhook_id == webhook_id)
                    .values(
                        failed_calls=Webhook.failed_calls + 1,
                        last_failure=config['last_failure']
                    )
                )
                session.commit()
        except Exception as e:
            logger.error(f"Failed to update webhook stats: {e}")
        
        logger.error(f"Webhook delivery failed after 3 attempts: {webhook_id}")
    
    def _load_webhooks(self):
        """Load webhooks from SQLite"""
        try:
            with self.SessionLocal() as session:
                webhooks = session.execute(select(Webhook)).scalars().all()
                
                for webhook in webhooks:
                    self.webhooks[webhook.webhook_id] = {
                        'url': webhook.url,
                        'events': json.loads(webhook.events),
                        'secret': webhook.secret,
                        'team': webhook.team,
                        'created_at': webhook.created_at.isoformat() if webhook.created_at else None,
                        'total_calls': webhook.total_calls,
                        'failed_calls': webhook.failed_calls,
                        'last_success': webhook.last_success,
                        'last_failure': webhook.last_failure,
                        'enabled': webhook.enabled
                    }
                
                logger.info(f"Loaded {len(self.webhooks)} webhooks from SQLite")
        except Exception as e:
            logger.error(f"Failed to load webhooks from SQLite: {e}")
            self.webhooks = {}


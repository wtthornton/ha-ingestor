"""
Simple Game Event Detector

Detects game events by comparing state changes.
Story 12.3 - Adaptive Event Monitor + Webhooks

Based on Context7 KB best practices.
"""

import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime


logger = logging.getLogger(__name__)


class GameEventDetector:
    """
    Simple event detector for game state changes.
    
    Following Context7 KB pattern:
    - Check every 15 seconds
    - Store previous state for comparison
    - Fire webhooks on events (game_started, score_changed, game_ended)
    """
    
    def __init__(self, sports_client, webhook_manager, check_interval: int = 15):
        """
        Initialize event detector.
        
        Args:
            sports_client: Sports API client
            webhook_manager: Webhook manager
            check_interval: Check interval in seconds (default 15)
        """
        self.sports_client = sports_client
        self.webhooks = webhook_manager
        self.check_interval = check_interval
        
        # Track previous game states
        self.previous_games: Dict[str, dict] = {}
        
        # Background task
        self.task = None
        self.is_running = False
    
    async def start(self):
        """Start background monitoring"""
        if self.is_running:
            return
        
        self.is_running = True
        self.task = asyncio.create_task(self._monitor_loop())
        logger.info(f"Event detector started (checking every {self.check_interval}s)")
    
    async def stop(self):
        """Stop background monitoring"""
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Event detector stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop - runs every 15 seconds"""
        while self.is_running:
            try:
                await self._check_for_events()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Event detection error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _check_for_events(self):
        """Check live games for state changes"""
        try:
            # Get current live games from both leagues
            nfl_games = await self.sports_client.get_live_games('nfl', [])
            nhl_games = await self.sports_client.get_live_games('nhl', [])
            
            all_games = nfl_games + nhl_games
            
            for game in all_games:
                game_id = game.get('id')
                if not game_id:
                    continue
                
                previous = self.previous_games.get(game_id)
                
                # Detect events
                if not previous:
                    # New game detected
                    if game.get('status') == 'live':
                        await self._trigger_event('game_started', game)
                else:
                    # Compare states
                    await self._compare_and_detect(previous, game)
                
                # Update state
                self.previous_games[game_id] = game
        
        except Exception as e:
            logger.error(f"Error checking for events: {e}")
    
    async def _compare_and_detect(self, previous: dict, current: dict):
        """Compare game states and detect events"""
        
        # Game started
        if previous.get('status') != 'live' and current.get('status') == 'live':
            await self._trigger_event('game_started', current)
        
        # Game ended
        elif previous.get('status') == 'live' and current.get('status') == 'final':
            await self._trigger_event('game_ended', current)
        
        # Score changed (during live game)
        elif current.get('status') == 'live':
            prev_score = previous.get('score', {})
            curr_score = current.get('score', {})
            
            if (prev_score.get('home') != curr_score.get('home') or 
                prev_score.get('away') != curr_score.get('away')):
                
                # Calculate score difference
                score_diff = {
                    'home_diff': curr_score.get('home', 0) - prev_score.get('home', 0),
                    'away_diff': curr_score.get('away', 0) - prev_score.get('away', 0),
                    'previous_score': prev_score,
                    'current_score': curr_score
                }
                
                await self._trigger_event('score_changed', current, extra=score_diff)
    
    async def _trigger_event(self, event_type: str, game: dict, extra: dict = None):
        """
        Trigger webhooks for event.
        
        Args:
            event_type: game_started, score_changed, game_ended
            game: Game data
            extra: Optional extra data (score diff)
        """
        event_data = {
            'event': event_type,
            'game_id': game.get('id'),
            'league': game.get('league'),
            'home_team': game.get('home_team', {}).get('abbreviation', 'unknown'),
            'away_team': game.get('away_team', {}).get('abbreviation', 'unknown'),
            'score': game.get('score', {}),
            'status': game.get('status'),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if extra:
            event_data.update(extra)
        
        # Fire webhooks (non-blocking)
        await self.webhooks.send_event(event_type, event_data)
        
        logger.info(f"Event: {event_type} for game {game.get('id')}")
    
    def _load_webhooks(self):
        """Load webhooks from JSON file"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    self.webhooks = json.load(f)
                logger.info(f"Loaded {len(self.webhooks)} webhooks")
        except Exception as e:
            logger.error(f"Failed to load webhooks: {e}")
            self.webhooks = {}
    
    def _save_webhooks(self):
        """Save webhooks to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, 'w') as f:
                json.dump(self.webhooks, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save webhooks: {e}")


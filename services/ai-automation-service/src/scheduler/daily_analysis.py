"""
Daily Analysis Scheduler
Runs pattern analysis and suggestion generation on a scheduled basis (default: 3 AM daily)
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timezone, timedelta
import logging
from typing import Optional, Dict
import asyncio

from ..clients.data_api_client import DataAPIClient
from ..clients.mqtt_client import MQTTNotificationClient
from ..pattern_analyzer.time_of_day import TimeOfDayPatternDetector
from ..pattern_analyzer.co_occurrence import CoOccurrencePatternDetector
from ..llm.openai_client import OpenAIClient
from ..database.crud import store_patterns, store_suggestion
from ..database.models import get_db, get_db_session
from ..config import settings

logger = logging.getLogger(__name__)


class DailyAnalysisScheduler:
    """Schedules and runs daily pattern analysis and suggestion generation"""
    
    def __init__(self, cron_schedule: Optional[str] = None):
        """
        Initialize the scheduler.
        
        Args:
            cron_schedule: Cron expression (default: "0 3 * * *" = 3 AM daily)
        """
        self.scheduler = AsyncIOScheduler()
        self.cron_schedule = cron_schedule or settings.analysis_schedule
        self.is_running = False
        self._job_history = []
        
        # Initialize MQTT client
        try:
            self.mqtt_client = MQTTNotificationClient(
                broker=settings.mqtt_broker,
                port=settings.mqtt_port
            )
            self.mqtt_client.connect()
        except Exception as e:
            logger.warning(f"⚠️ MQTT initialization failed: {e}. Notifications will be skipped.")
            self.mqtt_client = None
        
        logger.info(f"DailyAnalysisScheduler initialized with schedule: {self.cron_schedule}")
    
    def start(self):
        """
        Start the scheduler and register the daily analysis job.
        """
        try:
            # Add daily analysis job
            self.scheduler.add_job(
                self.run_daily_analysis,
                CronTrigger.from_crontab(self.cron_schedule),
                id='daily_pattern_analysis',
                name='Daily Pattern Analysis and Suggestion Generation',
                replace_existing=True,
                misfire_grace_time=3600  # Allow up to 1 hour late start
            )
            
            self.scheduler.start()
            logger.info(f"✅ Scheduler started: daily analysis at {self.cron_schedule}")
            logger.info(f"   Next run: {self.scheduler.get_job('daily_pattern_analysis').next_run_time}")
            
        except Exception as e:
            logger.error(f"❌ Failed to start scheduler: {e}", exc_info=True)
            raise
    
    def stop(self):
        """
        Stop the scheduler gracefully.
        """
        try:
            if self.scheduler.running:
                self.scheduler.shutdown(wait=True)
                logger.info("✅ Scheduler stopped")
            
            # Disconnect MQTT
            if self.mqtt_client:
                self.mqtt_client.disconnect()
                logger.info("✅ MQTT disconnected")
                
        except Exception as e:
            logger.error(f"❌ Failed to stop scheduler: {e}", exc_info=True)
    
    async def run_daily_analysis(self):
        """
        Main daily batch job workflow:
        1. Fetch historical events from Data API
        2. Run pattern detection (time-of-day + co-occurrence)
        3. Generate automation suggestions via OpenAI
        4. Store patterns and suggestions in database
        5. Log results and performance metrics
        
        This method is called by the scheduler automatically.
        """
        # Prevent concurrent runs
        if self.is_running:
            logger.warning("⚠️ Previous analysis still running, skipping this run")
            return
        
        self.is_running = True
        start_time = datetime.now(timezone.utc)
        job_result = {
            'start_time': start_time.isoformat(),
            'status': 'running'
        }
        
        try:
            logger.info("=" * 80)
            logger.info("🚀 Daily Analysis Job Started")
            logger.info("=" * 80)
            logger.info(f"Timestamp: {start_time.isoformat()}")
            
            # ================================================================
            # Phase 1: Fetch Events
            # ================================================================
            logger.info("📊 Phase 1: Fetching events from Data API...")
            
            data_client = DataAPIClient(
                base_url=settings.data_api_url,
                influxdb_url=settings.influxdb_url,
                influxdb_token=settings.influxdb_token,
                influxdb_org=settings.influxdb_org,
                influxdb_bucket=settings.influxdb_bucket
            )
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
            
            events_df = await data_client.fetch_events(
                start_time=start_date,
                limit=100000
            )
            
            if events_df.empty:
                logger.warning("❌ No events available for analysis")
                job_result['status'] = 'no_data'
                job_result['events_count'] = 0
                return
            
            logger.info(f"✅ Fetched {len(events_df)} events")
            job_result['events_count'] = len(events_df)
            
            # ================================================================
            # Phase 2: Pattern Detection
            # ================================================================
            logger.info("🔍 Phase 2: Detecting patterns...")
            
            all_patterns = []
            
            # Time-of-day patterns
            logger.info("  → Running time-of-day detector...")
            tod_detector = TimeOfDayPatternDetector(
                min_occurrences=5,
                min_confidence=0.7
            )
            
            # Time-of-day detector doesn't have optimized version
            tod_patterns = tod_detector.detect_patterns(events_df)
            
            all_patterns.extend(tod_patterns)
            logger.info(f"    ✅ Found {len(tod_patterns)} time-of-day patterns")
            
            # Co-occurrence patterns
            logger.info("  → Running co-occurrence detector...")
            co_detector = CoOccurrencePatternDetector(
                window_minutes=5,
                min_support=5,
                min_confidence=0.7
            )
            
            if len(events_df) > 50000:
                co_patterns = co_detector.detect_patterns_optimized(events_df)
            else:
                co_patterns = co_detector.detect_patterns(events_df)
            
            all_patterns.extend(co_patterns)
            logger.info(f"    ✅ Found {len(co_patterns)} co-occurrence patterns")
            logger.info(f"✅ Total patterns detected: {len(all_patterns)}")
            
            if not all_patterns:
                logger.warning("❌ No patterns detected")
                job_result['status'] = 'no_patterns'
                job_result['patterns_detected'] = 0
                return
            
            job_result['patterns_detected'] = len(all_patterns)
            
            # ================================================================
            # Phase 3: Store Patterns
            # ================================================================
            logger.info("💾 Phase 3: Storing patterns in database...")
            
            async with get_db_session() as db:
                patterns_stored = await store_patterns(db, all_patterns)
            
            logger.info(f"✅ Stored {patterns_stored} patterns")
            job_result['patterns_stored'] = patterns_stored
            
            # ================================================================
            # Phase 4: Generate Suggestions
            # ================================================================
            logger.info("🤖 Phase 4: Generating automation suggestions...")
            
            # Rank patterns by confidence and limit to top 10
            sorted_patterns = sorted(all_patterns, key=lambda p: p['confidence'], reverse=True)
            top_patterns = sorted_patterns[:10]
            
            logger.info(f"  → Processing top {len(top_patterns)} patterns")
            
            openai_client = OpenAIClient(api_key=settings.openai_api_key)
            suggestions_generated = 0
            suggestions_failed = 0
            
            for i, pattern in enumerate(top_patterns, 1):
                try:
                    logger.info(f"  → [{i}/{len(top_patterns)}] Generating suggestion: {pattern['device_id']}")
                    
                    suggestion = await openai_client.generate_automation_suggestion(pattern)
                    
                    # Store suggestion
                    async with get_db_session() as db:
                        await store_suggestion(db, {
                            'pattern_id': pattern.get('id'),
                            'title': suggestion.alias,
                            'description': suggestion.description,
                            'automation_yaml': suggestion.automation_yaml,
                            'confidence': pattern['confidence'],
                            'category': suggestion.category,
                            'priority': suggestion.priority
                        })
                    
                    suggestions_generated += 1
                    logger.info(f"    ✅ Stored suggestion: {suggestion.alias}")
                    
                except Exception as e:
                    logger.error(f"    ❌ Failed to generate suggestion: {e}")
                    suggestions_failed += 1
            
            logger.info(f"✅ Generated {suggestions_generated} suggestions")
            
            # OpenAI usage stats
            openai_cost = (
                (openai_client.total_input_tokens * 0.00000015) +
                (openai_client.total_output_tokens * 0.00000060)
            )
            logger.info(f"  → OpenAI tokens: {openai_client.total_tokens_used}")
            logger.info(f"  → OpenAI cost: ${openai_cost:.6f}")
            
            job_result['suggestions_generated'] = suggestions_generated
            job_result['suggestions_failed'] = suggestions_failed
            job_result['openai_tokens'] = openai_client.total_tokens_used
            job_result['openai_cost_usd'] = round(openai_cost, 6)
            
            # ================================================================
            # Phase 5: Publish Notification (MQTT)
            # ================================================================
            logger.info("📢 Phase 5: Publishing MQTT notification...")
            
            try:
                notification = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'patterns_detected': len(all_patterns),
                    'suggestions_generated': suggestions_generated,
                    'duration_seconds': (datetime.now(timezone.utc) - start_time).total_seconds(),
                    'success': True
                }
                
                if self.mqtt_client:
                    self.mqtt_client.publish_analysis_complete(notification)
                    logger.info("  ✅ MQTT notification published to ha-ai/analysis/complete")
                else:
                    logger.info("  ⚠️ MQTT client not available, skipping notification")
                    logger.info(f"  → Would have published: {notification}")
                
            except Exception as e:
                logger.warning(f"  ⚠️ Failed to publish MQTT notification: {e}")
            
            # ================================================================
            # Complete
            # ================================================================
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            job_result['status'] = 'success'
            job_result['end_time'] = end_time.isoformat()
            job_result['duration_seconds'] = round(duration, 2)
            
            logger.info("=" * 80)
            logger.info("✅ Daily Analysis Job Complete!")
            logger.info(f"  → Duration: {duration:.1f} seconds")
            logger.info(f"  → Events: {len(events_df)}")
            logger.info(f"  → Patterns: {len(all_patterns)}")
            logger.info(f"  → Suggestions: {suggestions_generated}")
            logger.info(f"  → Cost: ${openai_cost:.6f}")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"❌ Daily analysis job failed: {e}", exc_info=True)
            job_result['status'] = 'failed'
            job_result['error'] = str(e)
            job_result['end_time'] = datetime.now(timezone.utc).isoformat()
            
        finally:
            self.is_running = False
            self._store_job_history(job_result)
    
    def _store_job_history(self, job_result: Dict):
        """
        Store job execution history for tracking and debugging.
        
        Args:
            job_result: Dictionary with job execution details
        """
        # Keep last 30 job runs in memory
        self._job_history.append(job_result)
        if len(self._job_history) > 30:
            self._job_history.pop(0)
        
        logger.info(f"Job history updated: {job_result['status']}")
    
    def get_job_history(self, limit: int = 10) -> list:
        """
        Get recent job execution history.
        
        Args:
            limit: Maximum number of jobs to return
        
        Returns:
            List of recent job execution results
        """
        return self._job_history[-limit:]
    
    def get_next_run_time(self) -> Optional[datetime]:
        """
        Get the next scheduled run time.
        
        Returns:
            Next run time as datetime, or None if not scheduled
        """
        try:
            job = self.scheduler.get_job('daily_pattern_analysis')
            if job:
                return job.next_run_time
        except Exception as e:
            logger.error(f"Failed to get next run time: {e}")
        return None
    
    async def trigger_manual_run(self):
        """
        Manually trigger analysis run (for testing or on-demand execution).
        
        This runs in the background and doesn't block.
        """
        logger.info("🔧 Manual analysis run triggered")
        asyncio.create_task(self.run_daily_analysis())


"""
Miner Client

HTTP client for querying the Automation Miner corpus.

Context7-validated httpx async patterns with timeout and caching.
Epic AI-4, Story AI4.2
"""
import httpx
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MinerClient:
    """
    Client for Automation Miner API
    
    Features:
    - 100ms timeout (fail fast)
    - 7-day cache (corpus changes weekly)
    - Graceful degradation on failure
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8019",
        timeout: float = 0.1,  # 100ms
        cache_ttl_days: int = 7
    ):
        self.base_url = base_url
        self.timeout = httpx.Timeout(timeout)
        self.cache_ttl = timedelta(days=cache_ttl_days)
        
        # Simple in-memory cache
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
    
    def _get_cache_key(
        self,
        device: Optional[str],
        integration: Optional[str],
        use_case: Optional[str],
        min_quality: float
    ) -> str:
        """Generate cache key from query parameters"""
        return f"{device}:{integration}:{use_case}:{min_quality}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached result is still valid"""
        if cache_key not in self._cache_timestamps:
            return False
        
        age = datetime.utcnow() - self._cache_timestamps[cache_key]
        return age < self.cache_ttl
    
    async def search_corpus(
        self,
        device: Optional[str] = None,
        integration: Optional[str] = None,
        use_case: Optional[str] = None,
        min_quality: float = 0.8,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search community automation corpus
        
        Args:
            device: Filter by device type (e.g., "light", "motion_sensor")
            integration: Filter by integration (e.g., "mqtt", "zigbee2mqtt")
            use_case: Filter by use case (energy/comfort/security/convenience)
            min_quality: Minimum quality score (0.8 = high quality only)
            limit: Maximum results (default 5)
        
        Returns:
            List of automation dictionaries or empty list on failure
        """
        # Check cache
        cache_key = self._get_cache_key(device, integration, use_case, min_quality)
        
        if self._is_cache_valid(cache_key):
            logger.debug(f"Miner cache hit: {cache_key}")
            return self._cache[cache_key]
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    "min_quality": min_quality,
                    "limit": limit
                }
                
                if device:
                    params["device"] = device
                if integration:
                    params["integration"] = integration
                if use_case:
                    params["use_case"] = use_case
                
                response = await client.get(
                    f"{self.base_url}/api/automation-miner/corpus/search",
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                automations = data.get('automations', [])
                
                # Cache result
                self._cache[cache_key] = automations
                self._cache_timestamps[cache_key] = datetime.utcnow()
                
                logger.debug(
                    f"Miner query success: {len(automations)} results "
                    f"(device={device}, use_case={use_case})"
                )
                
                return automations
        
        except httpx.TimeoutException:
            logger.warning("Miner query timeout (>100ms) - graceful degradation")
            return []
        
        except httpx.HTTPError as e:
            logger.warning(f"Miner query HTTP error: {e} - graceful degradation")
            return []
        
        except Exception as e:
            logger.error(f"Miner query unexpected error: {e} - graceful degradation")
            return []
    
    async def invalidate_all_caches(self):
        """Clear all cached query results (called after weekly refresh)"""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("✅ All Miner caches invalidated")
    
    async def get_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get corpus statistics
        
        Returns:
            Stats dictionary or None on failure
        """
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:  # Longer timeout for stats
                response = await client.get(
                    f"{self.base_url}/api/automation-miner/corpus/stats"
                )
                response.raise_for_status()
                return response.json()
        
        except Exception as e:
            logger.warning(f"Failed to get Miner stats: {e}")
            return None


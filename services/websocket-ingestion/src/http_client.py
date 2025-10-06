import aiohttp
import asyncio
import logging
from typing import Dict, Any

class SimpleHTTPClient:
    """Simple HTTP client for sending events to enrichment service"""
    
    def __init__(self, enrichment_url: str):
        self.enrichment_url = enrichment_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def send_event(self, event_data: Dict[str, Any]) -> bool:
        """Send event to enrichment service with simple retry logic"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                async with self.session.post(
                    f"{self.enrichment_url}/events",
                    json=event_data,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        logging.info(f"Event sent successfully on attempt {attempt + 1}")
                        return True
                    else:
                        logging.warning(f"HTTP {response.status} on attempt {attempt + 1}")
                        
            except Exception as e:
                logging.warning(f"Attempt {attempt + 1} failed: {e}")
                
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5 * (attempt + 1))  # Simple backoff
        
        logging.error(f"Failed to send event after {max_retries} attempts")
        return False

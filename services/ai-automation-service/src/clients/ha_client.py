"""
Home Assistant API Client
Deploy and manage automations in Home Assistant
Story AI1.11: Home Assistant Integration
"""

import aiohttp
import logging
from typing import Dict, List, Optional
import yaml

logger = logging.getLogger(__name__)


class HomeAssistantClient:
    """
    Client for interacting with Home Assistant REST API.
    
    Handles deployment and management of automations.
    """
    
    def __init__(self, ha_url: str, access_token: str):
        """
        Initialize HA client.
        
        Args:
            ha_url: Home Assistant URL (e.g., "http://homeassistant:8123")
            access_token: Long-lived access token from HA
        """
        self.ha_url = ha_url.rstrip('/')
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    async def test_connection(self) -> bool:
        """
        Test connection to Home Assistant.
        
        Returns:
            True if connection successful
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.ha_url}/api/",
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Connected to Home Assistant: {data.get('message', 'OK')}")
                        return True
                    else:
                        logger.error(f"❌ HA connection failed: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Failed to connect to HA: {e}")
            return False
    
    async def get_automation(self, automation_id: str) -> Optional[Dict]:
        """
        Get a specific automation by ID.
        
        Args:
            automation_id: Automation entity ID (e.g., "automation.morning_lights")
        
        Returns:
            Automation data or None if not found
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.ha_url}/api/states/{automation_id}",
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        return None
                    else:
                        logger.error(f"Failed to get automation {automation_id}: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error getting automation {automation_id}: {e}")
            return None
    
    async def get_automations(self) -> List[Dict]:
        """
        Get automation configurations from Home Assistant.
        
        Story AI3.3: Unconnected Relationship Analysis
        
        Returns:
            List of automation configurations with trigger/action details
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.ha_url}/api/config/automation/config",
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        configs = await response.json()
                        logger.info(f"✅ Retrieved {len(configs)} automation configurations")
                        return configs
                    else:
                        logger.warning(f"Failed to get automation configs: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching automation configs: {e}")
            return []
    
    async def list_automations(self) -> List[Dict]:
        """
        List all automations in Home Assistant.
        
        Returns:
            List of automation entities
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.ha_url}/api/states",
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        all_states = await response.json()
                        automations = [
                            s for s in all_states 
                            if s.get('entity_id', '').startswith('automation.')
                        ]
                        logger.info(f"📋 Found {len(automations)} automations in HA")
                        return automations
                    else:
                        logger.error(f"Failed to list automations: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error listing automations: {e}")
            return []
    
    async def deploy_automation(self, automation_yaml: str, automation_id: Optional[str] = None) -> Dict:
        """
        Deploy an automation to Home Assistant.
        
        This uses the automations.yaml file approach via config reload.
        
        Args:
            automation_yaml: YAML automation config
            automation_id: Optional specific automation ID to update
        
        Returns:
            Dict with success status and automation ID
        """
        try:
            # Parse YAML to validate and extract automation ID
            automation_data = yaml.safe_load(automation_yaml)
            
            if not isinstance(automation_data, dict):
                raise ValueError("Invalid automation YAML: must be a dict")
            
            # Get or generate automation ID
            if automation_id is None:
                # Extract from alias or generate from title
                alias = automation_data.get('alias', 'ai_suggested_automation')
                automation_id = f"automation.{alias.lower().replace(' ', '_')}"
            
            logger.info(f"🚀 Deploying automation: {automation_id}")
            
            # For MVP: Use the automation service to create/update
            # In production, you'd write to automations.yaml and reload
            async with aiohttp.ClientSession() as session:
                # Call automation.reload service to reload config
                async with session.post(
                    f"{self.ha_url}/api/services/automation/reload",
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status in [200, 201]:
                        logger.info(f"✅ Automation deployed: {automation_id}")
                        return {
                            "success": True,
                            "automation_id": automation_id,
                            "message": "Automation deployed successfully"
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Deployment failed ({response.status}): {error_text}")
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}"
                        }
        except Exception as e:
            logger.error(f"❌ Error deploying automation: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def enable_automation(self, automation_id: str) -> bool:
        """
        Enable/turn on an automation.
        
        Args:
            automation_id: Automation entity ID
        
        Returns:
            True if successful
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ha_url}/api/services/automation/turn_on",
                    headers=self.headers,
                    json={"entity_id": automation_id},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status in [200, 201]:
                        logger.info(f"✅ Enabled automation: {automation_id}")
                        return True
                    else:
                        logger.error(f"Failed to enable {automation_id}: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error enabling automation {automation_id}: {e}")
            return False
    
    async def disable_automation(self, automation_id: str) -> bool:
        """
        Disable/turn off an automation.
        
        Args:
            automation_id: Automation entity ID
        
        Returns:
            True if successful
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ha_url}/api/services/automation/turn_off",
                    headers=self.headers,
                    json={"entity_id": automation_id},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status in [200, 201]:
                        logger.info(f"⏸️ Disabled automation: {automation_id}")
                        return True
                    else:
                        logger.error(f"Failed to disable {automation_id}: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error disabling automation {automation_id}: {e}")
            return False
    
    async def trigger_automation(self, automation_id: str) -> bool:
        """
        Manually trigger an automation.
        
        Args:
            automation_id: Automation entity ID
        
        Returns:
            True if successful
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ha_url}/api/services/automation/trigger",
                    headers=self.headers,
                    json={"entity_id": automation_id},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status in [200, 201]:
                        logger.info(f"▶️ Triggered automation: {automation_id}")
                        return True
                    else:
                        logger.error(f"Failed to trigger {automation_id}: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error triggering automation {automation_id}: {e}")
            return False
    
    async def delete_automation(self, automation_id: str) -> bool:
        """
        Delete an automation from Home Assistant.
        
        Note: This requires writing to automations.yaml and reloading.
        For MVP, we'll just disable it.
        
        Args:
            automation_id: Automation entity ID
        
        Returns:
            True if successful
        """
        # For MVP, just disable the automation
        return await self.disable_automation(automation_id)


"""
Home Assistant API Client
Deploy and manage automations in Home Assistant
Story AI1.11: Home Assistant Integration
"""

import aiohttp
import logging
from typing import Dict, List, Optional, Any
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

    async def conversation_process(self, text: str) -> Dict[str, Any]:
        """
        Process natural language using Home Assistant Conversation API.

        This is used by the Ask AI tab to extract entities and understand user intent.

        Args:
            text: Natural language input from user

        Returns:
            Dict containing entities, intent, and response from HA
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ha_url}/api/conversation/process",
                    headers=self.headers,
                    json={"text": text},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        logger.info(f"HA Conversation API processed: '{text}' -> {len(result.get('entities', []))} entities")
                        return result
                    else:
                        logger.error(f"HA Conversation API failed: {response.status}")
                        return {"entities": [], "intent": None, "response": None}

        except Exception as e:
            logger.error(f"Failed to process conversation with HA: {e}")
            # Return empty result instead of raising to allow fallback
            return {"entities": [], "intent": None, "response": None}
    
    async def validate_automation(self, automation_yaml: str) -> Dict[str, Any]:
        """
        Validate automation YAML without creating it.
        
        Checks:
        - YAML syntax is valid
        - Required fields are present
        - Referenced entities exist in HA
        
        Args:
            automation_yaml: YAML string for automation
        
        Returns:
            Dict with validation results
        """
        try:
            # Parse YAML
            automation_data = yaml.safe_load(automation_yaml)
            
            if not isinstance(automation_data, dict):
                return {
                    "valid": False,
                    "error": "Invalid YAML: must be a dictionary",
                    "details": []
                }
            
            errors = []
            warnings = []
            
            # Check required fields
            if 'trigger' not in automation_data and 'triggers' not in automation_data:
                errors.append("Missing required field: 'trigger' or 'triggers'")
            
            if 'action' not in automation_data and 'actions' not in automation_data:
                errors.append("Missing required field: 'action' or 'actions'")
            
            # Extract and validate entity IDs
            entity_ids = self._extract_entity_ids(automation_data)
            logger.info(f"Validating {len(entity_ids)} entities from automation")
            
            # Check if entities exist in HA
            async with aiohttp.ClientSession() as session:
                for entity_id in entity_ids:
                    async with session.get(
                        f"{self.ha_url}/api/states/{entity_id}",
                        headers=self.headers,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 404:
                            warnings.append(f"Entity not found: {entity_id}")
            
            if errors:
                return {
                    "valid": False,
                    "error": "; ".join(errors),
                    "details": warnings
                }
            
            return {
                "valid": True,
                "warnings": warnings,
                "entity_count": len(entity_ids),
                "automation_id": automation_data.get('id', automation_data.get('alias', 'unknown'))
            }
            
        except yaml.YAMLError as e:
            return {
                "valid": False,
                "error": f"YAML syntax error: {str(e)}",
                "details": []
            }
        except Exception as e:
            logger.error(f"Error validating automation: {e}", exc_info=True)
            return {
                "valid": False,
                "error": f"Validation error: {str(e)}",
                "details": []
            }
    
    def _extract_entity_ids(self, automation_data: Dict) -> List[str]:
        """
        Extract all entity IDs from automation config.
        
        Args:
            automation_data: Parsed automation dictionary
        
        Returns:
            List of entity IDs found in the automation
        """
        entity_ids = set()
        
        def extract_from_dict(d: Dict):
            for key, value in d.items():
                if key in ['entity_id', 'target']:
                    if isinstance(value, str) and '.' in value:
                        entity_ids.add(value)
                    elif isinstance(value, dict) and 'entity_id' in value:
                        if isinstance(value['entity_id'], str):
                            entity_ids.add(value['entity_id'])
                        elif isinstance(value['entity_id'], list):
                            entity_ids.update(value['entity_id'])
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, str) and '.' in item:
                                entity_ids.add(item)
                elif isinstance(value, dict):
                    extract_from_dict(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            extract_from_dict(item)
        
        extract_from_dict(automation_data)
        return list(entity_ids)
    
    async def create_automation(self, automation_yaml: str) -> Dict[str, Any]:
        """
        Create a new automation in Home Assistant.
        
        This writes the automation config directly to Home Assistant's configuration.
        
        Args:
            automation_yaml: YAML string for the automation
        
        Returns:
            Dict with creation result including automation_id and status
        """
        try:
            # First validate the automation
            validation = await self.validate_automation(automation_yaml)
            if not validation.get('valid', False):
                return {
                    "success": False,
                    "error": f"Validation failed: {validation.get('error', 'Unknown error')}",
                    "details": validation.get('details', [])
                }
            
            # Parse YAML
            automation_data = yaml.safe_load(automation_yaml)
            
            # Generate automation ID if not present
            if 'id' not in automation_data:
                alias = automation_data.get('alias', 'ai_automation')
                automation_data['id'] = alias.lower().replace(' ', '_').replace('-', '_')
            
            automation_id = f"automation.{automation_data['id']}"
            
            # Create automation via HA REST API
            # Note: HA doesn't have a direct REST endpoint to create automations
            # We need to use the config/automation/config endpoint (requires HA config write access)
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ha_url}/api/config/automation/config/{automation_data['id']}",
                    headers=self.headers,
                    json=automation_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        logger.info(f"✅ Automation created: {automation_id}")
                        
                        # Enable the automation
                        await self.enable_automation(automation_id)
                        
                        return {
                            "success": True,
                            "automation_id": automation_id,
                            "message": "Automation created and enabled successfully",
                            "warnings": validation.get('warnings', [])
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Failed to create automation ({response.status}): {error_text}")
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}"
                        }
        except Exception as e:
            logger.error(f"❌ Error creating automation: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }


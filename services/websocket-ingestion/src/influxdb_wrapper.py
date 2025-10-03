"""
InfluxDB Client for Time-Series Data Storage
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json

try:
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS
    from influxdb_client.client.exceptions import InfluxDBError
except ImportError:
    # Fallback for development without InfluxDB
    InfluxDBClient = None
    Point = None
    WritePrecision = None
    SYNCHRONOUS = None
    ASYNCHRONOUS = None
    InfluxDBError = Exception

logger = logging.getLogger(__name__)


class InfluxDBConnectionManager:
    """Manages InfluxDB connection with automatic reconnection"""
    
    def __init__(self, 
                 url: str, 
                 token: str, 
                 org: str, 
                 bucket: str,
                 timeout: int = 30,
                 retry_attempts: int = 3,
                 retry_delay: float = 1.0):
        """
        Initialize InfluxDB connection manager
        
        Args:
            url: InfluxDB server URL
            token: InfluxDB authentication token
            org: InfluxDB organization
            bucket: InfluxDB bucket name
            timeout: Connection timeout in seconds
            retry_attempts: Number of retry attempts on failure
            retry_delay: Delay between retry attempts in seconds
        """
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        
        # Connection management
        self.client: Optional[InfluxDBClient] = None
        self.write_api = None
        self.query_api = None
        self.is_connected = False
        
        # Statistics
        self.connection_attempts = 0
        self.successful_connections = 0
        self.failed_connections = 0
        self.last_connection_time: Optional[datetime] = None
        self.last_error: Optional[str] = None
        
        # Health monitoring
        self.last_health_check: Optional[datetime] = None
        self.health_check_interval = 60  # seconds
        self.health_check_task: Optional[asyncio.Task] = None
        self.is_running = False
    
    async def start(self):
        """Start the InfluxDB connection manager"""
        if self.is_running:
            logger.warning("InfluxDB connection manager is already running")
            return
        
        self.is_running = True
        
        # Start connection
        await self._connect()
        
        # Start health check task
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        
        logger.info("InfluxDB connection manager started")
    
    async def stop(self):
        """Stop the InfluxDB connection manager"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Stop health check task
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        
        # Close connection
        await self._disconnect()
        
        logger.info("InfluxDB connection manager stopped")
    
    async def _connect(self) -> bool:
        """Establish connection to InfluxDB"""
        try:
            self.connection_attempts += 1
            
            # Create InfluxDB client
            self.client = InfluxDBClient(
                url=self.url,
                token=self.token,
                org=self.org,
                timeout=self.timeout * 1000  # Convert to milliseconds
            )
            
            # Test connection
            await self._test_connection()
            
            # Initialize APIs
            self.write_api = self.client.write_api(write_options=ASYNCHRONOUS)
            self.query_api = self.client.query_api()
            
            self.is_connected = True
            self.successful_connections += 1
            self.last_connection_time = datetime.now()
            self.last_error = None
            
            logger.info("Successfully connected to InfluxDB")
            return True
            
        except Exception as e:
            self.failed_connections += 1
            self.last_error = str(e)
            self.is_connected = False
            
            logger.error(f"Failed to connect to InfluxDB: {e}")
            return False
    
    async def _test_connection(self):
        """Test InfluxDB connection"""
        if not self.client:
            raise Exception("Client not initialized")
        
        # Test connection by querying buckets
        query_api = self.client.query_api()
        query = f'import "influxdata/influxdb/schema"\n\nschema.buckets()'
        
        # Execute query with timeout
        await asyncio.wait_for(
            asyncio.to_thread(query_api.query, query, org=self.org),
            timeout=self.timeout
        )
    
    async def _disconnect(self):
        """Disconnect from InfluxDB"""
        try:
            if self.write_api:
                self.write_api.close()
                self.write_api = None
            
            if self.query_api:
                self.query_api = None
            
            if self.client:
                self.client.close()
                self.client = None
            
            self.is_connected = False
            logger.info("Disconnected from InfluxDB")
            
        except Exception as e:
            logger.error(f"Error disconnecting from InfluxDB: {e}")
    
    async def _health_check_loop(self):
        """Health check loop"""
        while self.is_running:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                if not self.is_running:
                    break
                
                await self._perform_health_check()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
    
    async def _perform_health_check(self):
        """Perform health check"""
        try:
            if not self.is_connected:
                # Try to reconnect
                await self._connect()
            else:
                # Test existing connection
                await self._test_connection()
            
            self.last_health_check = datetime.now()
            
        except Exception as e:
            logger.warning(f"InfluxDB health check failed: {e}")
            self.is_connected = False
    
    async def write_points(self, points: List[Point]) -> bool:
        """
        Write points to InfluxDB
        
        Args:
            points: List of InfluxDB Point objects
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected or not self.write_api:
            logger.error("InfluxDB not connected")
            return False
        
        try:
            # Write points asynchronously
            await asyncio.to_thread(
                self.write_api.write,
                bucket=self.bucket,
                org=self.org,
                record=points
            )
            
            logger.debug(f"Successfully wrote {len(points)} points to InfluxDB")
            return True
            
        except Exception as e:
            logger.error(f"Error writing points to InfluxDB: {e}")
            self.last_error = str(e)
            return False
    
    async def query_data(self, query: str) -> List[Dict[str, Any]]:
        """
        Query data from InfluxDB
        
        Args:
            query: InfluxDB query string
            
        Returns:
            List of query results
        """
        if not self.is_connected or not self.query_api:
            logger.error("InfluxDB not connected")
            return []
        
        try:
            # Execute query
            result = await asyncio.to_thread(
                self.query_api.query,
                query,
                org=self.org
            )
            
            # Convert result to list of dictionaries
            data = []
            for table in result:
                for record in table.records:
                    data.append({
                        "time": record.get_time(),
                        "measurement": record.get_measurement(),
                        "tags": record.values,
                        "fields": record.values
                    })
            
            logger.debug(f"Successfully queried {len(data)} records from InfluxDB")
            return data
            
        except Exception as e:
            logger.error(f"Error querying InfluxDB: {e}")
            self.last_error = str(e)
            return []
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get connection status"""
        return {
            "is_connected": self.is_connected,
            "url": self.url,
            "org": self.org,
            "bucket": self.bucket,
            "connection_attempts": self.connection_attempts,
            "successful_connections": self.successful_connections,
            "failed_connections": self.failed_connections,
            "last_connection_time": self.last_connection_time.isoformat() if self.last_connection_time else None,
            "last_error": self.last_error,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "health_check_interval": self.health_check_interval,
            "timeout": self.timeout,
            "retry_attempts": self.retry_attempts,
            "retry_delay": self.retry_delay
        }
    
    def configure_health_check_interval(self, interval: int):
        """Configure health check interval"""
        if interval <= 0:
            raise ValueError("Health check interval must be positive")
        
        self.health_check_interval = interval
        logger.info(f"Updated health check interval to {interval}s")
    
    def configure_retry_settings(self, attempts: int, delay: float):
        """Configure retry settings"""
        if attempts < 0:
            raise ValueError("Retry attempts must be non-negative")
        if delay < 0:
            raise ValueError("Retry delay must be non-negative")
        
        self.retry_attempts = attempts
        self.retry_delay = delay
        logger.info(f"Updated retry settings: attempts={attempts}, delay={delay}s")
    
    def reset_statistics(self):
        """Reset connection statistics"""
        self.connection_attempts = 0
        self.successful_connections = 0
        self.failed_connections = 0
        self.last_connection_time = None
        self.last_error = None
        self.last_health_check = None
        logger.info("InfluxDB connection statistics reset")

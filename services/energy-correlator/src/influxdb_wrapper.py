"""
InfluxDB Wrapper for Energy Correlator
Uses InfluxDB v2 client for queries (compatible with InfluxDB 2.7)
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

logger = logging.getLogger(__name__)


class InfluxDBWrapper:
    """Wrapper for InfluxDB operations using v2 client"""
    
    def __init__(
        self,
        influxdb_url: str,
        influxdb_token: str,
        influxdb_org: str,
        influxdb_bucket: str
    ):
        self.influxdb_url = influxdb_url
        self.influxdb_token = influxdb_token
        self.influxdb_org = influxdb_org
        self.influxdb_bucket = influxdb_bucket
        self.client: Optional[InfluxDBClient] = None
        self.write_api = None
        self.query_api = None
    
    def connect(self):
        """Initialize InfluxDB connection"""
        try:
            self.client = InfluxDBClient(
                url=self.influxdb_url,
                token=self.influxdb_token,
                org=self.influxdb_org
            )
            
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            
            logger.info(f"Connected to InfluxDB at {self.influxdb_url}")
            
        except Exception as e:
            logger.error(f"Failed to connect to InfluxDB: {e}")
            raise
    
    def close(self):
        """Close InfluxDB connection"""
        if self.client:
            try:
                if self.write_api:
                    self.write_api.close()
                self.client.close()
                logger.info("InfluxDB connection closed")
            except Exception as e:
                logger.error(f"Error closing InfluxDB connection: {e}")
    
    def query(self, flux_query: str) -> List[Dict]:
        """
        Execute Flux query and return results
        
        Args:
            flux_query: Flux query string
            
        Returns:
            List of records as dictionaries
        """
        try:
            tables = self.query_api.query(flux_query, org=self.influxdb_org)
            
            results = []
            for table in tables:
                for record in table.records:
                    # Convert record to dict
                    result = {
                        'time': record.get_time()
                    }
                    
                    # Add all values
                    for key, value in record.values.items():
                        if key not in ['result', 'table']:
                            result[key] = value
                    
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return []
    
    def write_point(self, point: Point):
        """
        Write a point to InfluxDB
        
        Args:
            point: InfluxDB Point object
        """
        try:
            self.write_api.write(
                bucket=self.influxdb_bucket,
                org=self.influxdb_org,
                record=point
            )
        except Exception as e:
            logger.error(f"Error writing point: {e}")
            raise


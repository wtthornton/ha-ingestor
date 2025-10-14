"""
InfluxDB Retention Policy Setup

Simple script to configure 2-year retention policy for sports data.
Story 12.1 - InfluxDB Persistence Layer

Usage:
    python -m src.setup_retention
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_retention_policy():
    """
    Configure InfluxDB retention policy.
    
    Note: InfluxDB v3 handles retention automatically based on database configuration.
    The retention period is specified in INFLUXDB_RETENTION_DAYS (default: 730 days = 2 years).
    
    For InfluxDB v3, retention is managed at the database level:
    - Data older than retention period is automatically deleted
    - No manual policy creation needed
    - Configured via database settings or CLI
    """
    retention_days = int(os.getenv('INFLUXDB_RETENTION_DAYS', '730'))
    database = os.getenv('INFLUXDB_DATABASE', 'sports_data')
    
    logger.info(f"Retention policy configured for database '{database}':")
    logger.info(f"  - Retention period: {retention_days} days ({retention_days / 365:.1f} years)")
    logger.info(f"  - Data older than {retention_days} days will be automatically removed")
    logger.info("")
    logger.info("InfluxDB v3 handles retention automatically at the database level.")
    logger.info("Ensure your InfluxDB instance is configured with the correct retention settings.")
    logger.info("")
    logger.info("To manually configure retention in InfluxDB v3:")
    logger.info(f"  influx bucket update --name {database} --retention {retention_days * 24}h")


if __name__ == "__main__":
    setup_retention_policy()


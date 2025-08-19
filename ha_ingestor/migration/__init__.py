"""Schema migration module for InfluxDB optimization.

This module provides comprehensive tools for migrating from the existing
InfluxDB schema to the new optimized schema, including:

- Schema migration orchestration
- Data extraction, transformation, and loading
- Migration validation and testing
- Test data generation for migration testing
"""

from .migration_scripts import (
    DataExtractor,
    DataLoader,
    DataTransformer,
    DataValidator,
    MigrationBatch,
    MigrationRunner,
)
from .schema_migration import (
    MigrationConfig,
    MigrationMetrics,
    MigrationPhase,
    MigrationStrategy,
    SchemaMigrator,
)
from .test_data_generator import (
    DataPattern,
    HomeAssistantDataGenerator,
    TestDataConfig,
    generate_test_data_for_migration,
)

__all__ = [
    # Schema migration
    "SchemaMigrator",
    "MigrationConfig",
    "MigrationPhase",
    "MigrationStrategy",
    "MigrationMetrics",
    # Migration scripts
    "DataExtractor",
    "DataTransformer",
    "DataLoader",
    "DataValidator",
    "MigrationBatch",
    "MigrationRunner",
    # Test data generation
    "HomeAssistantDataGenerator",
    "TestDataConfig",
    "DataPattern",
    "generate_test_data_for_migration",
]

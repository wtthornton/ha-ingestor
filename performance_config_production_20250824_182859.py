# HA-Ingestor Performance Configuration
# Generated on 2025-08-24 18:28:59
# Environment: production

# Migration Configuration
migration_config = {
    "strategy": "dual_write",
    "migration_window_hours": 24,
    "validation_window_hours": 72,
    "cleanup_delay_hours": 168,
    "batch_size": 1000,
    "concurrent_batches": 8,
    "throttle_delay_ms": 10,
    "max_error_rate": 0.01,
    "rollback_threshold": 0.02,
    "enable_metrics": True,
    "enable_alerts": True,
    "performance_monitoring": True
}

# Transformation Configuration
transformation_config = {
    "measurement_consolidation": True,
    "tag_optimization": True,
    "field_optimization": True,
    "compression_enabled": True,
    "batch_size": 1000,
    "concurrent_workers": 8
}

# Monitoring Configuration
monitoring_config = {
    "metrics_enabled": True,
    "health_check_interval": 30,
    "performance_tracking": True,
    "alerting_enabled": True
}

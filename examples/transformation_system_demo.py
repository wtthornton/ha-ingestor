#!/usr/bin/env python3
"""Demonstration of the Home Assistant Data Transformation System.

This script showcases the various transformation capabilities including:
- Field mapping and renaming
- Data type conversion and validation
- Custom transformation functions
- Rule-based transformation execution
- Transformation chains
"""

import json
import os
import sys
from datetime import date, datetime
from decimal import Decimal

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ha_ingestor.transformers.base import (
    TransformationChain,
    TransformationRule,
    TransformationType,
)
from ha_ingestor.transformers.custom_transformer import CustomTransformer
from ha_ingestor.transformers.field_mapper import FieldMapper
from ha_ingestor.transformers.rule_engine import TransformationRuleEngine
from ha_ingestor.transformers.type_converter import TypeConverter


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def print_subheader(title):
    """Print a formatted subheader."""
    print(f"\n--- {title} ---")


def demo_field_mapper():
    """Demonstrate field mapping capabilities."""
    print_header("Field Mapper Demonstration")

    # Sample Home Assistant event data
    sample_data = {
        "entity_id": "light.living_room",
        "domain": "light",
        "state": "on",
        "attributes": {
            "brightness": 255,
            "color_temp": 4000,
            "friendly_name": "Living Room Light",
        },
        "last_changed": "2024-01-01T12:00:00",
        "last_updated": "2024-01-01T12:00:00",
    }

    print("Original data:")
    print(json.dumps(sample_data, indent=2, default=str))

    # Create field mapper with various configurations
    field_mapper_config = {
        "field_mappings": {
            "entity_id": "device_id",
            "state": "current_state",
            "attributes.brightness": "brightness_level",
            "attributes.color_temp": "color_temperature",
            "attributes.friendly_name": "device_name",
        },
        "add_prefix": "ha_",
        "add_suffix": "_processed",
        "case_transform": "lower",
    }

    field_mapper = FieldMapper("home_assistant_mapper", field_mapper_config)

    print_subheader("Field Mapping Configuration")
    print(f"Field mappings: {field_mapper.get_field_mappings()}")
    print(f"Prefix: {field_mapper.add_prefix}")
    print(f"Suffix: {field_mapper.add_suffix}")
    print(f"Case transform: {field_mapper.case_transform}")

    # Apply transformation
    result = field_mapper.transform(sample_data)

    print_subheader("Transformation Result")
    if result.success:
        print("✅ Transformation successful!")
        print("Transformed data:")
        print(json.dumps(result.data, indent=2, default=str))
        print(f"\nMetadata: {result.metadata}")
        print(f"Processing time: {result.processing_time_ms:.2f}ms")
    else:
        print("❌ Transformation failed!")
        print(f"Errors: {result.errors}")

    # Show metrics
    print_subheader("Field Mapper Metrics")
    metrics = field_mapper.get_metrics()
    print(f"Total transformations: {metrics['transformations_total']}")
    print(f"Successful: {metrics['transformations_success']}")
    print(f"Failed: {metrics['transformations_failed']}")
    print(f"Total processing time: {metrics['total_processing_time_ms']:.2f}ms")


def demo_type_converter():
    """Demonstrate type conversion capabilities."""
    print_header("Type Converter Demonstration")

    # Sample data with various types
    sample_data = {
        "temperature": "22.5",
        "humidity": "45",
        "is_active": "true",
        "timestamp": "2024-01-01 12:00:00",
        "date_recorded": "2024-01-01",
        "pressure": "1013.25",
        "status_code": "200",
    }

    print("Original data:")
    print(json.dumps(sample_data, indent=2))

    # Create type converter with comprehensive configuration
    type_converter_config = {
        "type_mappings": {
            "temperature": "float",
            "humidity": "int",
            "is_active": "bool",
            "timestamp": "datetime",
            "date_recorded": "date",
            "pressure": "decimal",
            "status_code": "int",
        },
        "default_values": {"missing_field": "unknown"},
        "validation_rules": {
            "temperature": {"min_value": -50, "max_value": 100},
            "humidity": {"min_value": 0, "max_value": 100},
            "pressure": {"min_value": 800, "max_value": 1200},
        },
        "strict_mode": False,
        "handle_errors": "warn",
    }

    type_converter = TypeConverter("sensor_data_converter", type_converter_config)

    print_subheader("Type Conversion Configuration")
    print(f"Type mappings: {type_converter.get_type_mappings()}")
    print(f"Validation rules: {type_converter.get_validation_rules()}")
    print(f"Strict mode: {type_converter.strict_mode}")
    print(f"Error handling: {type_converter.handle_errors}")

    # Apply transformation
    result = type_converter.transform(sample_data)

    print_subheader("Transformation Result")
    if result.success:
        print("✅ Transformation successful!")
        print("Transformed data:")
        transformed_data = result.data.copy()
        # Format datetime objects for display
        for key, value in transformed_data.items():
            if isinstance(value, (datetime, date)):
                transformed_data[key] = str(value)
            elif isinstance(value, Decimal):
                transformed_data[key] = float(value)

        print(json.dumps(transformed_data, indent=2))
        print(f"\nMetadata: {result.metadata}")
        print(f"Processing time: {result.processing_time_ms:.2f}ms")

        if result.warnings:
            print(f"\nWarnings: {result.warnings}")
    else:
        print("❌ Transformation failed!")
        print(f"Errors: {result.errors}")

    # Show metrics
    print_subheader("Type Converter Metrics")
    metrics = type_converter.get_metrics()
    print(f"Total transformations: {metrics['transformations_total']}")
    print(f"Successful: {metrics['transformations_success']}")
    print(f"Failed: {metrics['transformations_failed']}")
    print(f"Total processing time: {metrics['total_processing_time_ms']:.2f}ms")


def demo_custom_transformer():
    """Demonstrate custom transformation capabilities."""
    print_header("Custom Transformer Demonstration")

    # Sample Home Assistant automation event
    sample_data = {
        "entity_id": "automation.morning_routine",
        "domain": "automation",
        "state": "on",
        "attributes": {
            "last_triggered": "2024-01-01T07:00:00",
            "mode": "single",
            "current": 0,
        },
        "context": {"user_id": "admin", "parent_id": None},
    }

    print("Original data:")
    print(json.dumps(sample_data, indent=2, default=str))

    # Custom transformation functions
    def pre_process(data, context, logger, transformer_name):
        """Pre-process the data to add metadata."""
        data["_processed_by"] = transformer_name
        data["_processing_timestamp"] = datetime.now().isoformat()
        return {"success": True, "data": data}

    def transform(data, context, logger, transformer_name):
        """Main transformation logic."""
        # Add business logic
        if data.get("domain") == "automation":
            data["automation_metrics"] = {
                "is_active": data.get("state") == "on",
                "trigger_count": data.get("attributes", {}).get("current", 0),
                "last_triggered": data.get("attributes", {}).get("last_triggered"),
            }

            # Add priority based on automation type
            if "morning" in data.get("entity_id", ""):
                data["priority"] = "high"
            elif "evening" in data.get("entity_id", ""):
                data["priority"] = "medium"
            else:
                data["priority"] = "low"

        return data

    def post_process(data, context, logger, transformer_name):
        """Post-process to add summary information."""
        data["_summary"] = {
            "total_fields": len(data),
            "has_automation_metrics": "automation_metrics" in data,
            "priority_level": data.get("priority", "unknown"),
        }
        return {"success": True, "data": data}

    def error_handler(error, data, function_name, context):
        """Custom error handler."""
        logger.error(f"Error in {function_name}: {error}")
        # Return fallback data
        data["_error"] = str(error)
        data["_error_function"] = function_name
        return {"success": True, "data": data}

    # Create custom transformer
    custom_transformer_config = {
        "pre_process_function": pre_process,
        "transform_function": transform,
        "post_process_function": post_process,
        "error_handler": error_handler,
        "function_context": {"environment": "production"},
    }

    custom_transformer = CustomTransformer(
        "automation_enhancer", custom_transformer_config
    )

    print_subheader("Custom Transformer Configuration")
    print(f"Has pre-process: {custom_transformer.pre_process_function is not None}")
    print(f"Has transform: {custom_transformer.transform_function is not None}")
    print(f"Has post-process: {custom_transformer.post_process_function is not None}")
    print(f"Has error handler: {custom_transformer.error_handler is not None}")
    print(f"Context: {custom_transformer.get_context()}")

    # Apply transformation
    result = custom_transformer.transform(sample_data)

    print_subheader("Transformation Result")
    if result.success:
        print("✅ Transformation successful!")
        print("Transformed data:")
        # Format datetime objects for display
        display_data = result.data.copy()
        for key, value in display_data.items():
            if isinstance(value, datetime):
                display_data[key] = str(value)

        print(json.dumps(display_data, indent=2))
        print(f"\nMetadata: {result.metadata}")
        print(f"Processing time: {result.processing_time_ms:.2f}ms")

        if result.warnings:
            print(f"\nWarnings: {result.warnings}")
    else:
        print("❌ Transformation failed!")
        print(f"Errors: {result.errors}")

    # Show metrics
    print_subheader("Custom Transformer Metrics")
    metrics = custom_transformer.get_metrics()
    print(f"Total transformations: {metrics['transformations_total']}")
    print(f"Successful: {metrics['transformations_success']}")
    print(f"Failed: {metrics['transformations_failed']}")
    print(f"Total processing time: {metrics['total_processing_time_ms']:.2f}ms")


def demo_transformation_chain():
    """Demonstrate transformation chain capabilities."""
    print_header("Transformation Chain Demonstration")

    # Sample data
    sample_data = {
        "entity_id": "switch.garage_door",
        "domain": "switch",
        "state": "off",
        "attributes": {"friendly_name": "Garage Door Switch", "icon": "mdi:garage"},
        "last_changed": "2024-01-01T18:30:00",
    }

    print("Original data:")
    print(json.dumps(sample_data, indent=2, default=str))

    # Create individual transformers
    field_mapper = FieldMapper(
        "field_renamer",
        {
            "field_mappings": {
                "entity_id": "device_id",
                "state": "current_state",
                "attributes.friendly_name": "device_name",
            },
            "add_prefix": "ha_",
        },
    )

    type_converter = TypeConverter(
        "type_converter", {"type_mappings": {"last_changed": "datetime"}}
    )

    def custom_transform(data, context, logger, transformer_name):
        """Add business logic."""
        if data.get("domain") == "switch":
            data["switch_metadata"] = {
                "is_garage_door": "garage" in data.get("ha_device_name", ""),
                "is_on": data.get("ha_current_state") == "on",
                "category": (
                    "security"
                    if "garage" in data.get("ha_device_name", "")
                    else "general"
                ),
            }
        return data

    custom_transformer = CustomTransformer(
        "business_logic", {"transform_function": custom_transform}
    )

    # Create transformation chain
    chain = TransformationChain("garage_door_processor")
    chain.add_transformer(field_mapper)
    chain.add_transformer(type_converter)
    chain.add_transformer(custom_transformer)

    print_subheader("Transformation Chain Configuration")
    print(f"Chain name: {chain.name}")
    print(f"Number of transformers: {len(chain.transformers)}")
    print("Transformers:")
    for transformer in chain.transformers:
        print(f"  - {transformer.name} ({type(transformer).__name__})")

    # Execute chain
    result = chain.transform(sample_data)

    print_subheader("Chain Execution Result")
    if result.success:
        print("✅ Chain execution successful!")
        print("Transformed data:")
        # Format datetime objects for display
        display_data = result.data.copy()
        for key, value in display_data.items():
            if isinstance(value, datetime):
                display_data[key] = str(value)

        print(json.dumps(display_data, indent=2))
        print(f"\nMetadata: {result.metadata}")
        print(f"Processing time: {result.processing_time_ms:.2f}ms")

        if result.warnings:
            print(f"\nWarnings: {result.warnings}")
    else:
        print("❌ Chain execution failed!")
        print(f"Errors: {result.errors}")

    # Show chain metrics
    print_subheader("Transformation Chain Metrics")
    metrics = chain.get_metrics()
    print(f"Chain executions total: {metrics['chain_executions_total']}")
    print(f"Successful: {metrics['chain_executions_success']}")
    print(f"Failed: {metrics['chain_executions_failed']}")
    print(f"Total processing time: {metrics['total_chain_processing_time_ms']:.2f}ms")
    print(f"Transformer count: {metrics['transformer_count']}")

    # Show individual transformer metrics
    print("\nIndividual transformer metrics:")
    for name, transformer_metrics in metrics["transformer_metrics"].items():
        print(
            f"  {name}: {transformer_metrics['transformations_total']} transformations"
        )


def demo_rule_engine():
    """Demonstrate rule engine capabilities."""
    print_header("Transformation Rule Engine Demonstration")

    # Create rule engine
    engine = TransformationRuleEngine("home_assistant_processor")

    # Define transformation rules
    rules = [
        # Field mapping rule for light entities
        TransformationRule(
            name="light_field_mapping",
            description="Map light entity fields to standardized format",
            transformation_type=TransformationType.FIELD_MAPPING,
            priority=10,
            config={
                "field_mappings": {
                    "entity_id": "device_id",
                    "state": "current_state",
                    "attributes.brightness": "brightness_level",
                },
                "add_prefix": "ha_",
            },
            conditions={"domain": "light"},
        ),
        # Type conversion rule for numeric fields
        TransformationRule(
            name="numeric_type_conversion",
            description="Convert numeric fields to appropriate types",
            transformation_type=TransformationType.TYPE_CONVERSION,
            priority=20,
            config={
                "type_mappings": {
                    "ha_brightness_level": "int",
                    "attributes.color_temp": "int",
                },
                "validation_rules": {
                    "ha_brightness_level": {"min_value": 0, "max_value": 255}
                },
            },
        ),
        # Custom transformation rule for business logic
        TransformationRule(
            name="light_business_logic",
            description="Add business logic for light entities",
            transformation_type=TransformationType.CUSTOM_FUNCTION,
            priority=30,
            config={
                "transform_function": lambda data: {
                    **data,
                    "light_metrics": {
                        "is_on": data.get("ha_current_state") == "on",
                        "has_brightness": "ha_brightness_level" in data,
                        "brightness_percentage": (
                            (data.get("ha_brightness_level", 0) / 255) * 100
                            if data.get("ha_brightness_level") is not None
                            else 0
                        ),
                    },
                }
            },
        ),
    ]

    # Add rules to engine
    for rule in rules:
        engine.add_rule(rule)
        print(f"Added rule: {rule.name} (priority: {rule.priority})")

    print_subheader("Rule Engine Configuration")
    print(f"Total rules: {len(engine.rules)}")
    print(f"Enabled rules: {len(engine.get_enabled_rules())}")

    # Sample light event data
    sample_data = {
        "entity_id": "light.living_room",
        "domain": "light",
        "state": "on",
        "attributes": {
            "brightness": "200",
            "color_temp": "4000",
            "friendly_name": "Living Room Light",
        },
    }

    print("\nSample data:")
    print(json.dumps(sample_data, indent=2))

    # Execute rules
    print_subheader("Rule Execution")
    transformed_data = engine.execute_rules(sample_data)

    print("Transformed data:")
    print(json.dumps(transformed_data, indent=2))

    # Show engine metrics
    print_subheader("Rule Engine Metrics")
    metrics = engine.get_engine_metrics()
    print(f"Total rules: {metrics['total_rules']}")
    print(f"Enabled rules: {metrics['enabled_rules']}")
    print(f"Total transformers: {metrics['total_transformers']}")
    print(f"Total chains: {metrics['total_chains']}")

    print("\nRules by type:")
    for rule_type, count in metrics["rules_by_type"].items():
        print(f"  {rule_type}: {count}")

    # Create and execute a transformation chain
    print_subheader("Creating Transformation Chain")
    chain = engine.create_chain_from_rules(
        "light_processor",
        ["light_field_mapping", "numeric_type_conversion", "light_business_logic"],
    )

    print(f"Created chain: {chain.name}")
    print(f"Transformers in chain: {len(chain.transformers)}")

    # Execute the chain
    chain_result = engine.execute_chain("light_processor", sample_data)

    print("\nChain execution result:")
    print(json.dumps(chain_result, indent=2))


def main():
    """Run all demonstrations."""
    print("🏠 Home Assistant Data Transformation System Demonstration")
    print("This script showcases the comprehensive transformation capabilities")
    print("for processing Home Assistant events and sensor data.")

    try:
        # Run all demonstrations
        demo_field_mapper()
        demo_type_converter()
        demo_custom_transformer()
        demo_transformation_chain()
        demo_rule_engine()

        print_header("Demonstration Complete")
        print("✅ All transformation system features demonstrated successfully!")
        print("\nKey features demonstrated:")
        print("• Field mapping and renaming with prefix/suffix support")
        print("• Data type conversion and validation")
        print("• Custom transformation functions with pre/post processing")
        print("• Transformation chains for complex workflows")
        print("• Rule-based transformation engine")
        print("• Comprehensive metrics and monitoring")
        print("• Error handling and recovery")

    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

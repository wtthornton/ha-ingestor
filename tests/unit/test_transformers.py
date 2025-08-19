"""Unit tests for the transformation system."""

import pytest
import time
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import Mock, patch

from ha_ingestor.transformers.base import (
    TransformationType, TransformationResult, TransformationRule, 
    Transformer, TransformationChain
)
from ha_ingestor.transformers.field_mapper import FieldMapper
from ha_ingestor.transformers.type_converter import TypeConverter
from ha_ingestor.transformers.custom_transformer import CustomTransformer
from ha_ingestor.transformers.rule_engine import TransformationRuleEngine


class TestTransformationResult:
    """Test TransformationResult dataclass."""
    
    def test_creation(self):
        """Test creating a TransformationResult."""
        result = TransformationResult(
            success=True,
            data={"test": "value"},
            errors=["error1"],
            warnings=["warning1"],
            metadata={"key": "value"},
            processing_time_ms=100.0
        )
        
        assert result.success is True
        assert result.data == {"test": "value"}
        assert result.errors == ["error1"]
        assert result.warnings == ["warning1"]
        assert result.metadata == {"key": "value"}
        assert result.processing_time_ms == 100.0
    
    def test_default_values(self):
        """Test TransformationResult with default values."""
        result = TransformationResult(success=True, data={})
        
        assert result.errors == []
        assert result.warnings == []
        assert result.metadata == {}
        assert result.processing_time_ms == 0.0


class TestTransformationRule:
    """Test TransformationRule model."""
    
    def test_creation(self):
        """Test creating a TransformationRule."""
        rule = TransformationRule(
            name="test_rule",
            description="Test rule",
            transformation_type=TransformationType.FIELD_MAPPING,
            enabled=True,
            priority=50,
            config={"field_mappings": {"old": "new"}},
            conditions={"domain": "light"}
        )
        
        assert rule.name == "test_rule"
        assert rule.description == "Test rule"
        assert rule.transformation_type == TransformationType.FIELD_MAPPING
        assert rule.enabled is True
        assert rule.priority == 50
        assert rule.config == {"field_mappings": {"old": "new"}}
        assert rule.conditions == {"domain": "light"}
    
    def test_default_values(self):
        """Test TransformationRule with default values."""
        rule = TransformationRule(
            name="test_rule",
            transformation_type=TransformationType.FIELD_MAPPING
        )
        
        assert rule.description is None
        assert rule.enabled is True
        assert rule.priority == 100
        assert rule.config == {}
        assert rule.conditions is None


class TestFieldMapper:
    """Test FieldMapper transformer."""
    
    def test_creation(self):
        """Test creating a FieldMapper."""
        config = {
            "field_mappings": {"old_field": "new_field"},
            "remove_unmapped": True,
            "add_prefix": "ha_",
            "add_suffix": "_processed",
            "case_transform": "lower"
        }
        
        mapper = FieldMapper("test_mapper", config)
        
        assert mapper.name == "test_mapper"
        assert mapper.field_mappings == {"old_field": "new_field"}
        assert mapper.remove_unmapped is True
        assert mapper.add_prefix == "ha_"
        assert mapper.add_suffix == "_processed"
        assert mapper.case_transform == "lower"
    
    def test_basic_field_mapping(self):
        """Test basic field mapping functionality."""
        config = {"field_mappings": {"old_field": "new_field"}}
        mapper = FieldMapper("test_mapper", config)
        
        data = {"old_field": "value", "other_field": "other_value"}
        result = mapper.transform(data)
        
        assert result.success is True
        assert result.data["new_field"] == "value"
        assert "old_field" not in result.data
        assert result.data["other_field"] == "other_value"
    
    def test_remove_unmapped_fields(self):
        """Test removing unmapped fields."""
        config = {
            "field_mappings": {"old_field": "new_field"},
            "remove_unmapped": True
        }
        mapper = FieldMapper("test_mapper", config)
        
        data = {"old_field": "value", "other_field": "other_value"}
        result = mapper.transform(data)
        
        assert result.success is True
        assert result.data["new_field"] == "value"
        assert "other_field" not in result.data
        assert len(result.data) == 1
    
    def test_add_prefix_and_suffix(self):
        """Test adding prefix and suffix to field names."""
        config = {
            "field_mappings": {"old_field": "new_field"},
            "add_prefix": "ha_",
            "add_suffix": "_processed"
        }
        mapper = FieldMapper("test_mapper", config)
        
        data = {"old_field": "value"}
        result = mapper.transform(data)
        
        assert result.success is True
        assert result.data["ha_new_field_processed"] == "value"
    
    def test_case_transformation(self):
        """Test case transformation of field names."""
        config = {
            "field_mappings": {"OldField": "NewField"},
            "case_transform": "lower"
        }
        mapper = FieldMapper("test_mapper", config)
        
        data = {"OldField": "value"}
        result = mapper.transform(data)
        
        assert result.success is True
        assert result.data["newfield"] == "value"
    
    def test_conditions_evaluation(self):
        """Test conditions evaluation."""
        config = {
            "field_mappings": {"old_field": "new_field"},
            "conditions": {"domain": "light"}
        }
        mapper = FieldMapper("test_mapper", config)
        
        # Should apply when domain matches
        data = {"domain": "light", "old_field": "value"}
        assert mapper.should_apply(data) is True
        
        # Should not apply when domain doesn't match
        data = {"domain": "switch", "old_field": "value"}
        assert mapper.should_apply(data) is False
    
    def test_invalid_input(self):
        """Test handling of invalid input."""
        config = {"field_mappings": {"old_field": "new_field"}}
        mapper = FieldMapper("test_mapper", config)
        
        result = mapper.transform("not_a_dict")
        
        assert result.success is False
        assert "must be a dictionary" in result.errors[0]


class TestTypeConverter:
    """Test TypeConverter transformer."""
    
    def test_creation(self):
        """Test creating a TypeConverter."""
        config = {
            "type_mappings": {"field1": "int", "field2": "float"},
            "default_values": {"field3": "default"},
            "validation_rules": {"field1": {"min_value": 0}},
            "strict_mode": True,
            "handle_errors": "fail"
        }
        
        converter = TypeConverter("test_converter", config)
        
        assert converter.name == "test_converter"
        assert converter.type_mappings == {"field1": "int", "field2": "float"}
        assert converter.default_values == {"field3": "default"}
        assert converter.validation_rules == {"field1": {"min_value": 0}}
        assert converter.strict_mode is True
        assert converter.handle_errors == "fail"
    
    def test_basic_type_conversion(self):
        """Test basic type conversion functionality."""
        config = {"type_mappings": {"string_field": "int", "float_field": "str"}}
        converter = TypeConverter("test_converter", config)
        
        data = {"string_field": "123", "float_field": 45.67}
        result = converter.transform(data)
        
        assert result.success is True
        assert result.data["string_field"] == 123
        assert result.data["float_field"] == "45.67"
    
    def test_datetime_conversion(self):
        """Test datetime conversion functionality."""
        config = {"type_mappings": {"timestamp": "datetime", "date_field": "date"}}
        converter = TypeConverter("test_converter", config)
        
        data = {
            "timestamp": "2024-01-01 12:00:00",
            "date_field": "2024-01-01"
        }
        result = converter.transform(data)
        
        assert result.success is True
        assert isinstance(result.data["timestamp"], datetime)
        assert isinstance(result.data["date_field"], date)
    
    def test_validation_rules(self):
        """Test validation rules functionality."""
        config = {
            "type_mappings": {"age": "int"},
            "validation_rules": {"age": {"min_value": 0, "max_value": 150}},
            "strict_mode": True
        }
        converter = TypeConverter("test_converter", config)
        
        # Valid value
        data = {"age": "25"}
        result = converter.transform(data)
        assert result.success is True
        
        # Invalid value (too low)
        data = {"age": "-5"}
        result = converter.transform(data)
        assert result.success is False
        assert "less than minimum" in result.errors[0]
    
    def test_default_values(self):
        """Test default value functionality."""
        config = {
            "type_mappings": {"missing_field": "str"},
            "default_values": {"missing_field": "default_value"}
        }
        converter = TypeConverter("test_converter", config)
        
        data = {}
        result = converter.transform(data)
        
        assert result.success is True
        assert result.data["missing_field"] == "default_value"
    
    def test_error_handling_modes(self):
        """Test different error handling modes."""
        # Test warn mode
        config = {
            "type_mappings": {"field": "int"},
            "handle_errors": "warn"
        }
        converter = TypeConverter("test_converter", config)
        
        data = {"field": "not_a_number"}
        result = converter.transform(data)
        
        assert result.success is True
        assert "not_a_number" in result.warnings[0]
        
        # Test fail mode
        config["handle_errors"] = "fail"
        converter = TypeConverter("test_converter", config)
        
        result = converter.transform(data)
        assert result.success is False
        assert "not_a_number" in result.errors[0]


class TestCustomTransformer:
    """Test CustomTransformer."""
    
    def test_creation(self):
        """Test creating a CustomTransformer."""
        def transform_func(data):
            return {"transformed": True}
        
        config = {"transform_function": transform_func}
        transformer = CustomTransformer("test_transformer", config)
        
        assert transformer.name == "test_transformer"
        assert transformer.transform_function == transform_func
    
    def test_basic_transformation(self):
        """Test basic custom transformation functionality."""
        def transform_func(data):
            data["processed"] = True
            return data
        
        config = {"transform_function": transform_func}
        transformer = CustomTransformer("test_transformer", config)
        
        data = {"original": "value"}
        result = transformer.transform(data)
        
        assert result.success is True
        assert result.data["processed"] is True
        assert result.data["original"] == "value"
    
    def test_pre_and_post_processing(self):
        """Test pre and post processing functionality."""
        def pre_func(data):
            data["pre_processed"] = True
            return {"success": True, "data": data}
        
        def post_func(data):
            data["post_processed"] = True
            return {"success": True, "data": data}
        
        config = {
            "pre_process_function": pre_func,
            "post_process_function": post_func
        }
        transformer = CustomTransformer("test_transformer", config)
        
        data = {"original": "value"}
        result = transformer.transform(data)
        
        assert result.success is True
        assert result.data["pre_processed"] is True
        assert result.data["post_processed"] is True
    
    def test_error_handling(self):
        """Test error handling functionality."""
        def error_handler(error, data, function_name, context):
            return {"success": True, "data": {"error_handled": True}}
        
        def failing_func(data):
            raise ValueError("Test error")
        
        config = {
            "transform_function": failing_func,
            "error_handler": error_handler
        }
        transformer = CustomTransformer("test_transformer", config)
        
        data = {"original": "value"}
        result = transformer.transform(data)
        
        assert result.success is True
        assert result.data["error_handled"] is True


class TestTransformationChain:
    """Test TransformationChain."""
    
    def test_creation(self):
        """Test creating a TransformationChain."""
        chain = TransformationChain("test_chain")
        
        assert chain.name == "test_chain"
        assert len(chain.transformers) == 0
    
    def test_adding_transformers(self):
        """Test adding transformers to the chain."""
        chain = TransformationChain("test_chain")
        
        transformer1 = Mock(spec=Transformer)
        transformer1.name = "transformer1"
        transformer1.transform.return_value = TransformationResult(
            success=True, data={"field1": "value1"}, processing_time_ms=10.0
        )
        
        transformer2 = Mock(spec=Transformer)
        transformer2.name = "transformer2"
        transformer2.transform.return_value = TransformationResult(
            success=True, data={"field2": "value2"}, processing_time_ms=15.0
        )
        
        chain.add_transformer(transformer1)
        chain.add_transformer(transformer2)
        
        assert len(chain.transformers) == 2
    
    def test_chain_execution(self):
        """Test executing a transformation chain."""
        chain = TransformationChain("test_chain")
        
        # Mock transformers
        transformer1 = Mock(spec=Transformer)
        transformer1.name = "transformer1"
        transformer1.should_apply.return_value = True
        transformer1.transform.return_value = TransformationResult(
            success=True, data={"field1": "value1", "field2": "value2"}, processing_time_ms=10.0
        )
        
        transformer2 = Mock(spec=Transformer)
        transformer2.name = "transformer2"
        transformer2.should_apply.return_value = True
        transformer2.transform.return_value = TransformationResult(
            success=True, data={"field1": "value1", "field2": "value2", "field3": "value3"}, processing_time_ms=15.0
        )
        
        chain.add_transformer(transformer1)
        chain.add_transformer(transformer2)
        
        data = {"field1": "value1"}
        result = chain.transform(data)
        
        assert result.success is True
        assert result.data["field3"] == "value3"
        assert len(chain.transformers) == 2
    
    def test_chain_metrics(self):
        """Test chain metrics collection."""
        chain = TransformationChain("test_chain")
        
        transformer = Mock(spec=Transformer)
        transformer.name = "transformer1"
        transformer.should_apply.return_value = True
        transformer.transform.return_value = TransformationResult(
            success=True, data={"field1": "value1"}, processing_time_ms=10.0
        )
        transformer.get_metrics.return_value = {"transformations_total": 1}
        
        chain.add_transformer(transformer)
        chain.transform({"field1": "value1"})
        
        metrics = chain.get_metrics()
        assert metrics["chain_executions_total"] == 1
        assert metrics["chain_executions_success"] == 1
        assert metrics["transformer_count"] == 1


class TestTransformationRuleEngine:
    """Test TransformationRuleEngine."""
    
    def test_creation(self):
        """Test creating a TransformationRuleEngine."""
        engine = TransformationRuleEngine("test_engine")
        
        assert engine.name == "test_engine"
        assert len(engine.rules) == 0
        assert len(engine.transformers) == 0
        assert len(engine.chains) == 0
    
    def test_adding_rules(self):
        """Test adding transformation rules."""
        engine = TransformationRuleEngine("test_engine")
        
        rule = TransformationRule(
            name="test_rule",
            transformation_type=TransformationType.FIELD_MAPPING,
            config={"field_mappings": {"old": "new"}}
        )
        
        engine.add_rule(rule)
        
        assert len(engine.rules) == 1
        assert engine.rules[0].name == "test_rule"
    
    def test_rule_priority_sorting(self):
        """Test that rules are sorted by priority."""
        engine = TransformationRuleEngine("test_engine")
        
        rule1 = TransformationRule(
            name="high_priority",
            transformation_type=TransformationType.FIELD_MAPPING,
            priority=100
        )
        
        rule2 = TransformationRule(
            name="low_priority",
            transformation_type=TransformationType.FIELD_MAPPING,
            priority=50
        )
        
        engine.add_rule(rule1)
        engine.add_rule(rule2)
        
        # Lower priority number = higher precedence
        assert engine.rules[0].name == "low_priority"
        assert engine.rules[1].name == "high_priority"
    
    def test_creating_transformers_from_rules(self):
        """Test creating transformers from rules."""
        engine = TransformationRuleEngine("test_engine")
        
        rule = TransformationRule(
            name="test_rule",
            transformation_type=TransformationType.FIELD_MAPPING,
            config={"field_mappings": {"old": "new"}}
        )
        
        engine.add_rule(rule)
        transformer = engine.create_transformer_from_rule(rule)
        
        assert isinstance(transformer, FieldMapper)
        assert transformer.name == "test_rule"
        assert transformer in engine.transformers.values()
    
    def test_executing_rules(self):
        """Test executing transformation rules."""
        engine = TransformationRuleEngine("test_engine")
        
        rule = TransformationRule(
            name="test_rule",
            transformation_type=TransformationType.FIELD_MAPPING,
            config={"field_mappings": {"old_field": "new_field"}}
        )
        
        engine.add_rule(rule)
        
        data = {"old_field": "value", "other_field": "other_value"}
        result = engine.execute_rules(data)
        
        assert result["new_field"] == "value"
        assert "old_field" not in result
        assert result["other_field"] == "other_value"
    
    def test_conditions_evaluation(self):
        """Test rule conditions evaluation."""
        engine = TransformationRuleEngine("test_engine")
        
        rule = TransformationRule(
            name="test_rule",
            transformation_type=TransformationType.FIELD_MAPPING,
            config={"field_mappings": {"old": "new"}},
            conditions={"domain": "light"}
        )
        
        engine.add_rule(rule)
        
        # Should apply when domain matches
        data = {"domain": "light", "old": "value"}
        result = engine.execute_rules(data)
        assert "new" in result
        
        # Should not apply when domain doesn't match
        data = {"domain": "switch", "old": "value"}
        result = engine.execute_rules(data)
        assert "new" not in result
    
    def test_creating_chains(self):
        """Test creating transformation chains."""
        engine = TransformationRuleEngine("test_engine")
        
        # Add rules
        rule1 = TransformationRule(
            name="rule1",
            transformation_type=TransformationType.FIELD_MAPPING,
            config={"field_mappings": {"field1": "new_field1"}}
        )
        
        rule2 = TransformationRule(
            name="rule2",
            transformation_type=TransformationType.FIELD_MAPPING,
            config={"field_mappings": {"field2": "new_field2"}}
        )
        
        engine.add_rule(rule1)
        engine.add_rule(rule2)
        
        # Create chain
        chain = engine.create_chain_from_rules("test_chain", ["rule1", "rule2"])
        
        assert chain.name == "test_chain"
        assert len(chain.transformers) == 2
        assert "test_chain" in engine.chains
    
    def test_engine_metrics(self):
        """Test engine metrics collection."""
        engine = TransformationRuleEngine("test_engine")
        
        # Add a rule and execute it
        rule = TransformationRule(
            name="test_rule",
            transformation_type=TransformationType.FIELD_MAPPING,
            config={"field_mappings": {"old": "new"}}
        )
        
        engine.add_rule(rule)
        engine.execute_rules({"old": "value"})
        
        metrics = engine.get_engine_metrics()
        
        assert metrics["total_rules"] == 1
        assert metrics["enabled_rules"] == 1
        assert metrics["total_transformers"] == 1
        assert "test_rule" in metrics["transformer_metrics"]


if __name__ == "__main__":
    pytest.main([__file__])

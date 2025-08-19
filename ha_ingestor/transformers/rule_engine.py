"""Rule engine for managing and executing transformation rules."""

from typing import Any, Dict, List, Optional, Union
import structlog
from .base import TransformationRule, TransformationType, Transformer, TransformationChain
from .field_mapper import FieldMapper
from .type_converter import TypeConverter
from .custom_transformer import CustomTransformer


class TransformationRuleEngine:
    """Engine for managing and executing transformation rules."""
    
    def __init__(self, name: str = "default"):
        self.name = name
        self.logger = structlog.get_logger(f"{__name__}.{name}")
        self.rules: List[TransformationRule] = []
        self.transformers: Dict[str, Transformer] = {}
        self.chains: Dict[str, TransformationChain] = {}
        
        self.logger.info("TransformationRuleEngine initialized", name=name)
    
    def add_rule(self, rule: TransformationRule) -> None:
        """Add a transformation rule to the engine."""
        # Validate rule
        if not rule.name:
            raise ValueError("Rule must have a name")
        
        # Check for duplicate names
        if any(r.name == rule.name for r in self.rules):
            raise ValueError(f"Rule with name '{rule.name}' already exists")
        
        # Sort rules by priority (lower priority = higher precedence)
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority)
        
        self.logger.info("Added transformation rule", 
                        rule_name=rule.name,
                        rule_type=rule.transformation_type,
                        priority=rule.priority)
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove a transformation rule by name."""
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                del self.rules[i]
                self.logger.info("Removed transformation rule", rule_name=rule_name)
                return True
        return False
    
    def get_rule(self, rule_name: str) -> Optional[TransformationRule]:
        """Get a transformation rule by name."""
        for rule in self.rules:
            if rule.name == rule_name:
                return rule
        return None
    
    def get_rules_by_type(self, rule_type: TransformationType) -> List[TransformationRule]:
        """Get all rules of a specific type."""
        return [rule for rule in self.rules if rule.transformation_type == rule_type and rule.enabled]
    
    def get_enabled_rules(self) -> List[TransformationRule]:
        """Get all enabled rules."""
        return [rule for rule in self.rules if rule.enabled]
    
    def create_transformer_from_rule(self, rule: TransformationRule) -> Transformer:
        """Create a transformer instance from a transformation rule."""
        if rule.name in self.transformers:
            return self.transformers[rule.name]
        
        if rule.transformation_type == TransformationType.FIELD_MAPPING:
            transformer = FieldMapper(rule.name, rule.config)
        elif rule.transformation_type == TransformationType.TYPE_CONVERSION:
            transformer = TypeConverter(rule.name, rule.config)
        elif rule.transformation_type == TransformationType.CUSTOM_FUNCTION:
            transformer = CustomTransformer(rule.name, rule.config)
        else:
            raise ValueError(f"Unsupported transformation type: {rule.transformation_type}")
        
        # Store the transformer
        self.transformers[rule.name] = transformer
        
        self.logger.info("Created transformer from rule", 
                        rule_name=rule.name,
                        transformer_type=type(transformer).__name__)
        
        return transformer
    
    def create_chain_from_rules(self, chain_name: str, rule_names: List[str]) -> TransformationChain:
        """Create a transformation chain from a list of rule names."""
        if chain_name in self.chains:
            return self.chains[chain_name]
        
        chain = TransformationChain(chain_name)
        
        for rule_name in rule_names:
            rule = self.get_rule(rule_name)
            if rule and rule.enabled:
                transformer = self.create_transformer_from_rule(rule)
                chain.add_transformer(transformer)
            else:
                self.logger.warning("Rule not found or disabled", rule_name=rule_name)
        
        # Store the chain
        self.chains[chain_name] = chain
        
        self.logger.info("Created transformation chain", 
                        chain_name=chain_name,
                        rules_count=len(rule_names))
        
        return chain
    
    def execute_rules(self, data: Dict[str, Any], rule_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute transformation rules on data."""
        if rule_names is None:
            # Execute all enabled rules
            rules_to_execute = self.get_enabled_rules()
        else:
            # Execute specific rules
            rules_to_execute = []
            for name in rule_names:
                rule = self.get_rule(name)
                if rule and rule.enabled:
                    rules_to_execute.append(rule)
                else:
                    self.logger.warning("Rule not found or disabled", rule_name=name)
        
        if not rules_to_execute:
            self.logger.warning("No rules to execute")
            return data
        
        # Sort rules by priority
        rules_to_execute.sort(key=lambda r: r.priority)
        
        # Execute rules sequentially
        current_data = data.copy()
        executed_rules = []
        errors = []
        warnings = []
        
        for rule in rules_to_execute:
            try:
                # Check if rule should be applied
                if rule.conditions:
                    if not self._evaluate_conditions(rule.conditions, current_data):
                        self.logger.debug("Rule conditions not met", rule_name=rule.name)
                        continue
                
                # Create or get transformer
                transformer = self.create_transformer_from_rule(rule)
                
                # Execute transformation
                result = transformer.transform(current_data)
                
                if result.success:
                    current_data = result.data
                    executed_rules.append({
                        "name": rule.name,
                        "type": rule.transformation_type,
                        "success": True,
                        "processing_time_ms": result.processing_time_ms
                    })
                    
                    if result.warnings:
                        warnings.extend([f"{rule.name}: {w}" for w in result.warnings])
                    
                    self.logger.debug("Rule executed successfully", 
                                    rule_name=rule.name,
                                    processing_time_ms=result.processing_time_ms)
                else:
                    executed_rules.append({
                        "name": rule.name,
                        "type": rule.transformation_type,
                        "success": False,
                        "errors": result.errors
                    })
                    
                    if result.errors:
                        errors.extend([f"{rule.name}: {e}" for e in result.errors])
                    
                    if result.warnings:
                        warnings.extend([f"{rule.name}: {w}" for w in result.warnings])
                    
                    self.logger.warning("Rule execution failed", 
                                      rule_name=rule.name,
                                      errors=result.errors)
                    
                    # Stop execution if stop_on_error is enabled
                    if rule.config.get("stop_on_error", True):
                        break
            
            except Exception as e:
                error_msg = f"Rule '{rule.name}' failed with exception: {str(e)}"
                errors.append(error_msg)
                executed_rules.append({
                    "name": rule.name,
                    "type": rule.transformation_type,
                    "success": False,
                    "error": str(e)
                })
                
                self.logger.error("Rule execution failed with exception", 
                                rule_name=rule.name,
                                error=str(e))
                
                # Stop execution if stop_on_error is enabled
                if rule.config.get("stop_on_error", True):
                    break
        
        # Log execution summary
        self.logger.info("Rule execution completed", 
                        rules_executed=len(executed_rules),
                        successful_rules=len([r for r in executed_rules if r["success"]]),
                        failed_rules=len([r for r in executed_rules if not r["success"]]),
                        errors_count=len(errors),
                        warnings_count=len(warnings))
        
        return current_data
    
    def execute_chain(self, chain_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a transformation chain by name."""
        if chain_name not in self.chains:
            raise ValueError(f"Transformation chain '{chain_name}' not found")
        
        chain = self.chains[chain_name]
        result = chain.transform(data)
        
        if result.success:
            self.logger.info("Chain execution completed successfully", 
                            chain_name=chain_name,
                            processing_time_ms=result.processing_time_ms)
        else:
            self.logger.warning("Chain execution completed with errors", 
                               chain_name=chain_name,
                               errors_count=len(result.errors),
                               processing_time_ms=result.processing_time_ms)
        
        return result.data
    
    def _evaluate_conditions(self, conditions: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Evaluate rule conditions against data."""
        for condition_type, condition_value in conditions.items():
            if condition_type == "required_fields":
                if not all(field in data for field in condition_value):
                    return False
            
            elif condition_type == "excluded_fields":
                if any(field in data for field in condition_value):
                    return False
            
            elif condition_type == "domain":
                if data.get("domain") != condition_value:
                    return False
            
            elif condition_type == "entity_id":
                if data.get("entity_id") != condition_value:
                    return False
            
            elif condition_type == "custom_condition" and callable(condition_value):
                try:
                    if not condition_value(data):
                        return False
                except Exception as e:
                    self.logger.warning("Custom condition evaluation failed", error=str(e))
                    return False
        
        return True
    
    def load_rules_from_config(self, config: Dict[str, Any]) -> None:
        """Load transformation rules from configuration."""
        rules_config = config.get("transformation_rules", [])
        
        for rule_config in rules_config:
            try:
                rule = TransformationRule(**rule_config)
                self.add_rule(rule)
            except Exception as e:
                self.logger.error("Failed to load rule from config", 
                                rule_config=rule_config,
                                error=str(e))
        
        self.logger.info("Loaded rules from configuration", rules_count=len(rules_config))
    
    def get_engine_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics for the rule engine."""
        metrics = {
            "total_rules": len(self.rules),
            "enabled_rules": len(self.get_enabled_rules()),
            "total_transformers": len(self.transformers),
            "total_chains": len(self.chains),
            "rules_by_type": {},
            "transformer_metrics": {},
            "chain_metrics": {}
        }
        
        # Count rules by type
        for rule_type in TransformationType:
            metrics["rules_by_type"][rule_type.value] = len(self.get_rules_by_type(rule_type))
        
        # Collect transformer metrics
        for name, transformer in self.transformers.items():
            metrics["transformer_metrics"][name] = transformer.get_metrics()
        
        # Collect chain metrics
        for name, chain in self.chains.items():
            metrics["chain_metrics"][name] = chain.get_metrics()
        
        return metrics
    
    def reset_metrics(self) -> None:
        """Reset metrics for all transformers and chains."""
        for transformer in self.transformers.values():
            transformer.reset_metrics()
        
        for chain in self.chains.values():
            chain.reset_metrics()
        
        self.logger.info("Reset all metrics")
    
    def export_configuration(self) -> Dict[str, Any]:
        """Export the current rule engine configuration."""
        config = {
            "engine_name": self.name,
            "rules": [rule.dict() for rule in self.rules],
            "chains": {}
        }
        
        # Export chain configurations
        for chain_name, chain in self.chains.items():
            config["chains"][chain_name] = {
                "transformers": [t.name for t in chain.transformers]
            }
        
        return config
    
    def import_configuration(self, config: Dict[str, Any]) -> None:
        """Import configuration into the rule engine."""
        # Clear existing configuration
        self.rules.clear()
        self.transformers.clear()
        self.chains.clear()
        
        # Import rules
        if "rules" in config:
            for rule_config in config["rules"]:
                try:
                    rule = TransformationRule(**rule_config)
                    self.add_rule(rule)
                except Exception as e:
                    self.logger.error("Failed to import rule", 
                                    rule_config=rule_config,
                                    error=str(e))
        
        # Import chains
        if "chains" in config:
            for chain_name, chain_config in config["chains"].items():
                if "transformers" in chain_config:
                    self.create_chain_from_rules(chain_name, chain_config["transformers"])
        
        self.logger.info("Configuration imported successfully", 
                        rules_count=len(self.rules),
                        chains_count=len(self.chains))

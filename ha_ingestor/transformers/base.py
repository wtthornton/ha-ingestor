"""Base classes for the data transformation system."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class TransformationType(str, Enum):
    """Types of transformations that can be applied."""
    FIELD_MAPPING = "field_mapping"
    TYPE_CONVERSION = "type_conversion"
    CUSTOM_FUNCTION = "custom_function"
    VALIDATION = "validation"
    ENRICHMENT = "enrichment"


@dataclass
class TransformationResult:
    """Result of a transformation operation."""
    success: bool
    data: Dict[str, Any]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time_ms: float = 0.0


class TransformationRule(BaseModel):
    """Configuration for a transformation rule."""
    name: str = Field(..., description="Unique name for the transformation rule")
    description: Optional[str] = Field(None, description="Description of what this rule does")
    transformation_type: TransformationType = Field(..., description="Type of transformation")
    enabled: bool = Field(True, description="Whether this rule is active")
    priority: int = Field(100, description="Priority for rule execution order (lower = higher priority)")
    
    # Rule-specific configuration
    config: Dict[str, Any] = Field(default_factory=dict, description="Configuration specific to transformation type")
    
    # Conditions for when to apply this rule
    conditions: Optional[Dict[str, Any]] = Field(None, description="Conditions that must be met to apply this rule")
    
    # Validation
    class Config:
        use_enum_values = True


class Transformer(ABC):
    """Abstract base class for all transformers."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.logger = structlog.get_logger(f"{__name__}.{name}")
        self.metrics = {
            "transformations_total": 0,
            "transformations_success": 0,
            "transformations_failed": 0,
            "total_processing_time_ms": 0.0,
        }
    
    @abstractmethod
    def transform(self, data: Dict[str, Any]) -> TransformationResult:
        """Transform the input data according to the transformer's logic."""
        pass
    
    def should_apply(self, data: Dict[str, Any]) -> bool:
        """Determine if this transformer should be applied to the given data."""
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for this transformer."""
        return self.metrics.copy()
    
    def reset_metrics(self) -> None:
        """Reset performance metrics."""
        self.metrics = {
            "transformations_total": 0,
            "transformations_success": 0,
            "transformations_failed": 0,
            "total_processing_time_ms": 0.0,
        }


class TransformationChain:
    """Chains multiple transformers together for sequential processing."""
    
    def __init__(self, name: str):
        self.name = name
        self.transformers: List[Transformer] = []
        self.logger = structlog.get_logger(f"{__name__}.{name}")
        self.metrics = {
            "chain_executions_total": 0,
            "chain_executions_success": 0,
            "chain_executions_failed": 0,
            "total_chain_processing_time_ms": 0.0,
            "transformer_metrics": {},
        }
    
    def add_transformer(self, transformer: Transformer) -> None:
        """Add a transformer to the chain."""
        self.transformers.append(transformer)
        self.logger.info("Added transformer to chain", transformer=transformer.name)
    
    def remove_transformer(self, transformer_name: str) -> bool:
        """Remove a transformer from the chain by name."""
        for i, transformer in enumerate(self.transformers):
            if transformer.name == transformer_name:
                del self.transformers[i]
                self.logger.info("Removed transformer from chain", transformer=transformer_name)
                return True
        return False
    
    def transform(self, data: Dict[str, Any]) -> TransformationResult:
        """Execute the transformation chain on the input data."""
        start_time = time.time()
        self.metrics["chain_executions_total"] += 1
        
        try:
            current_data = data.copy()
            errors = []
            warnings = []
            metadata = {"chain_name": self.name, "transformers_applied": []}
            
            for transformer in self.transformers:
                if not transformer.should_apply(current_data):
                    self.logger.debug("Skipping transformer", transformer=transformer.name, reason="conditions_not_met")
                    continue
                
                try:
                    result = transformer.transform(current_data)
                    if result.success:
                        current_data = result.data
                        metadata["transformers_applied"].append({
                            "name": transformer.name,
                            "success": True,
                            "processing_time_ms": result.processing_time_ms
                        })
                        
                        # Collect warnings
                        if result.warnings:
                            warnings.extend([f"{transformer.name}: {w}" for w in result.warnings])
                    else:
                        errors.extend([f"{transformer.name}: {e}" for e in result.errors])
                        if result.warnings:
                            warnings.extend([f"{transformer.name}: {w}" for w in result.warnings])
                        
                        metadata["transformers_applied"].append({
                            "name": transformer.name,
                            "success": False,
                            "errors": result.errors
                        })
                        
                        # Stop chain execution on critical errors
                        if self.config.get("stop_on_error", True):
                            break
                            
                except Exception as e:
                    error_msg = f"Transformer {transformer.name} failed with exception: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error("Transformer execution failed", 
                                    transformer=transformer.name, error=str(e))
                    
                    metadata["transformers_applied"].append({
                        "name": transformer.name,
                        "success": False,
                        "error": str(e)
                    })
                    
                    if self.config.get("stop_on_error", True):
                        break
            
            processing_time = (time.time() - start_time) * 1000
            self.metrics["total_chain_processing_time_ms"] += processing_time
            
            if not errors:
                self.metrics["chain_executions_success"] += 1
                return TransformationResult(
                    success=True,
                    data=current_data,
                    warnings=warnings,
                    metadata=metadata,
                    processing_time_ms=processing_time
                )
            else:
                self.metrics["chain_executions_failed"] += 1
                return TransformationResult(
                    success=False,
                    data=current_data,
                    errors=errors,
                    warnings=warnings,
                    metadata=metadata,
                    processing_time_ms=processing_time
                )
                
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self.metrics["total_chain_processing_time_ms"] += processing_time
            self.metrics["chain_executions_failed"] += 1
            
            error_msg = f"Transformation chain failed with exception: {str(e)}"
            self.logger.error("Transformation chain execution failed", error=str(e))
            
            return TransformationResult(
                success=False,
                data=data,
                errors=[error_msg],
                metadata={"chain_name": self.name, "error": str(e)},
                processing_time_ms=processing_time
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the transformation chain."""
        # Collect metrics from individual transformers
        transformer_metrics = {}
        for transformer in self.transformers:
            transformer_metrics[transformer.name] = transformer.get_metrics()
        
        metrics = self.metrics.copy()
        metrics["transformer_metrics"] = transformer_metrics
        metrics["transformer_count"] = len(self.transformers)
        
        return metrics
    
    def reset_metrics(self) -> None:
        """Reset performance metrics for the chain and all transformers."""
        self.metrics = {
            "chain_executions_total": 0,
            "chain_executions_success": 0,
            "chain_executions_failed": 0,
            "total_chain_processing_time_ms": 0.0,
            "transformer_metrics": {},
        }
        
        for transformer in self.transformers:
            transformer.reset_metrics()

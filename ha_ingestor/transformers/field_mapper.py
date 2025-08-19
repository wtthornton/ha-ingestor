"""Field mapping transformer for renaming and restructuring data fields."""

import time
from typing import Any

from .base import TransformationResult, Transformer


class FieldMapper(Transformer):
    """Transforms data by mapping and renaming fields according to configuration."""

    def __init__(self, name: str, config: dict[str, Any] | None = None):
        super().__init__(name, config)

        # Field mapping configuration
        self.field_mappings: dict[str, str] = self.config.get("field_mappings", {})
        self.remove_unmapped: bool = self.config.get("remove_unmapped", False)
        self.add_prefix: str = self.config.get("add_prefix", "")
        self.add_suffix: str = self.config.get("add_suffix", "")
        self.case_transform: str = self.config.get(
            "case_transform", "none"
        )  # none, lower, upper, title

        # Validation
        if not isinstance(self.field_mappings, dict):
            raise ValueError("field_mappings must be a dictionary")

        self.logger.info(
            "FieldMapper initialized",
            mappings_count=len(self.field_mappings),
            remove_unmapped=self.remove_unmapped,
            add_prefix=self.add_prefix,
            add_suffix=self.add_suffix,
            case_transform=self.case_transform,
        )

    def transform(self, data: Any) -> TransformationResult:
        """Transform data by applying field mappings."""
        start_time = time.time()
        self.metrics["transformations_total"] += 1

        try:
            if not isinstance(data, dict):
                error_msg = (
                    f"Input data must be a dictionary, got {type(data).__name__}"
                )
                self.metrics["transformations_failed"] += 1
                return TransformationResult(
                    success=False,
                    data=data,
                    errors=[error_msg],
                    processing_time_ms=(time.time() - start_time) * 1000,
                )

            # Apply field mappings
            transformed_data = {}
            warnings = []

            # Process mapped fields
            for source_field, target_field in self.field_mappings.items():
                if source_field in data:
                    # Apply case transformation to target field name
                    transformed_target = self._apply_case_transform(target_field)

                    # Add prefix/suffix if configured
                    if self.add_prefix:
                        transformed_target = f"{self.add_prefix}{transformed_target}"
                    if self.add_suffix:
                        transformed_target = f"{transformed_target}{self.add_suffix}"

                    transformed_data[transformed_target] = data[source_field]
                    self.logger.debug(
                        "Mapped field",
                        source=source_field,
                        target=transformed_target,
                        value=data[source_field],
                    )
                else:
                    warning_msg = f"Source field '{source_field}' not found in data"
                    warnings.append(warning_msg)
                    self.logger.warning("Source field not found", field=source_field)

            # Handle unmapped fields
            if not self.remove_unmapped:
                for field_name, field_value in data.items():
                    if field_name not in self.field_mappings:
                        # Apply case transformation and prefix/suffix to unmapped fields
                        transformed_name = self._apply_case_transform(field_name)
                        if self.add_prefix:
                            transformed_name = f"{self.add_prefix}{transformed_name}"
                        if self.add_suffix:
                            transformed_name = f"{transformed_name}{self.add_suffix}"

                        transformed_data[transformed_name] = field_value

            processing_time = (time.time() - start_time) * 1000
            self.metrics["transformations_success"] += 1
            self.metrics["total_processing_time_ms"] += processing_time

            self.logger.info(
                "Field mapping completed",
                input_fields=len(data),
                output_fields=len(transformed_data),
                processing_time_ms=processing_time,
            )

            return TransformationResult(
                success=True,
                data=transformed_data,
                warnings=warnings,
                metadata={
                    "input_fields": len(data),
                    "output_fields": len(transformed_data),
                    "mappings_applied": len(self.field_mappings),
                    "unmapped_fields_preserved": not self.remove_unmapped,
                },
                processing_time_ms=processing_time,
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self.metrics["transformations_failed"] += 1
            self.metrics["total_processing_time_ms"] += processing_time

            error_msg = f"Field mapping failed: {str(e)}"
            self.logger.error("Field mapping transformation failed", error=str(e))

            return TransformationResult(
                success=False,
                data=data,
                errors=[error_msg],
                processing_time_ms=processing_time,
            )

    def _apply_case_transform(self, field_name: str) -> str:
        """Apply case transformation to field names."""
        if self.case_transform == "lower":
            return field_name.lower()
        elif self.case_transform == "upper":
            return field_name.upper()
        elif self.case_transform == "title":
            return field_name.title()
        else:
            return field_name

    def should_apply(self, data: dict[str, Any]) -> bool:
        """Check if this transformer should be applied based on conditions."""
        if not self.config.get("conditions"):
            return True

        conditions = self.config["conditions"]

        # Check if any required fields exist
        if "required_fields" in conditions:
            required_fields = conditions["required_fields"]
            if not all(field in data for field in required_fields):
                return False

        # Check if any excluded fields are present
        if "excluded_fields" in conditions:
            excluded_fields = conditions["excluded_fields"]
            if any(field in data for field in excluded_fields):
                return False

        # Check domain/entity conditions for Home Assistant events
        if "domain" in conditions:
            domain = conditions["domain"]
            if data.get("domain") != domain:
                return False

        if "entity_id" in conditions:
            entity_id = conditions["entity_id"]
            if data.get("entity_id") != entity_id:
                return False

        return True

    def add_field_mapping(self, source_field: str, target_field: str) -> None:
        """Add a new field mapping."""
        self.field_mappings[source_field] = target_field
        self.logger.info(
            "Added field mapping", source=source_field, target=target_field
        )

    def remove_field_mapping(self, source_field: str) -> bool:
        """Remove a field mapping."""
        if source_field in self.field_mappings:
            del self.field_mappings[source_field]
            self.logger.info("Removed field mapping", source=source_field)
            return True
        return False

    def get_field_mappings(self) -> dict[str, str]:
        """Get current field mappings."""
        return self.field_mappings.copy()

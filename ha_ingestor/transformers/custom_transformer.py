"""Custom transformer for applying user-defined transformation functions."""

import time
from collections.abc import Callable
from typing import Any

from .base import TransformationResult, Transformer


class CustomTransformer(Transformer):
    """Transforms data using custom Python functions provided by the user."""

    def __init__(self, name: str, config: dict[str, Any] | None = None):
        super().__init__(name, config)

        # Custom function configuration
        self.transform_function: Callable | None = self.config.get("transform_function")
        self.pre_process_function: Callable | None = self.config.get(
            "pre_process_function"
        )
        self.post_process_function: Callable | None = self.config.get(
            "post_process_function"
        )
        self.error_handler: Callable | None = self.config.get("error_handler")
        self.function_context: dict[str, Any] = self.config.get("function_context", {})

        # Validation
        if (
            not self.transform_function
            and not self.pre_process_function
            and not self.post_process_function
        ):
            raise ValueError("At least one transformation function must be provided")

        if self.transform_function and not callable(self.transform_function):
            raise ValueError("transform_function must be callable")

        if self.pre_process_function and not callable(self.pre_process_function):
            raise ValueError("pre_process_function must be callable")

        if self.post_process_function and not callable(self.post_process_function):
            raise ValueError("post_process_function must be callable")

        if self.error_handler and not callable(self.error_handler):
            raise ValueError("error_handler must be callable")

        self.logger.info(
            "CustomTransformer initialized",
            has_transform=bool(self.transform_function),
            has_pre_process=bool(self.pre_process_function),
            has_post_process=bool(self.post_process_function),
            has_error_handler=bool(self.error_handler),
        )

    def transform(self, data: Any) -> TransformationResult:
        """Transform data using custom functions."""
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

            current_data = data.copy()
            errors: list[str] = []
            warnings: list[str] = []
            metadata: dict[str, Any] = {"functions_executed": []}

            # Execute pre-processing function
            if self.pre_process_function:
                try:
                    pre_result = self._execute_function(
                        self.pre_process_function, current_data, "pre_process"
                    )
                    if pre_result["success"]:
                        current_data = pre_result["data"]
                        metadata["functions_executed"].append(
                            {
                                "function": "pre_process",
                                "success": True,
                                "execution_time_ms": pre_result["execution_time_ms"],
                            }
                        )

                        if pre_result.get("warnings"):
                            warnings.extend(pre_result["warnings"])
                    else:
                        errors.extend(pre_result["errors"])
                        if pre_result.get("warnings"):
                            warnings.extend(pre_result["warnings"])

                        metadata["functions_executed"].append(
                            {
                                "function": "pre_process",
                                "success": False,
                                "errors": pre_result["errors"],
                            }
                        )

                        # Stop execution if pre-processing fails and stop_on_error is enabled
                        if self.config.get("stop_on_error", True):
                            raise Exception("Pre-processing failed")

                except Exception as e:
                    error_msg = f"Pre-processing function failed: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error("Pre-processing function failed", error=str(e))

                    metadata["functions_executed"].append(
                        {"function": "pre_process", "success": False, "error": str(e)}
                    )

                    if self.config.get("stop_on_error", True):
                        raise

            # Execute main transformation function
            if self.transform_function and not errors:
                try:
                    transform_result = self._execute_function(
                        self.transform_function, current_data, "transform"
                    )
                    if transform_result["success"]:
                        current_data = transform_result["data"]
                        metadata["functions_executed"].append(
                            {
                                "function": "transform",
                                "success": True,
                                "execution_time_ms": transform_result[
                                    "execution_time_ms"
                                ],
                            }
                        )

                        if transform_result.get("warnings"):
                            warnings.extend(transform_result["warnings"])
                    else:
                        errors.extend(transform_result["errors"])
                        if transform_result.get("warnings"):
                            warnings.extend(transform_result["warnings"])

                        metadata["functions_executed"].append(
                            {
                                "function": "transform",
                                "success": False,
                                "errors": transform_result["errors"],
                            }
                        )

                        if self.config.get("stop_on_error", True):
                            raise Exception("Transformation failed")

                except Exception as e:
                    error_msg = f"Transformation function failed: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error("Transformation function failed", error=str(e))

                    metadata["functions_executed"].append(
                        {"function": "transform", "success": False, "error": str(e)}
                    )

                    if self.config.get("stop_on_error", True):
                        raise

            # Execute post-processing function
            if self.post_process_function and not errors:
                try:
                    post_result = self._execute_function(
                        self.post_process_function, current_data, "post_process"
                    )
                    if post_result["success"]:
                        current_data = post_result["data"]
                        metadata["functions_executed"].append(
                            {
                                "function": "post_process",
                                "success": True,
                                "execution_time_ms": post_result["execution_time_ms"],
                            }
                        )

                        if post_result.get("warnings"):
                            warnings.extend(post_result["warnings"])
                    else:
                        errors.extend(post_result["errors"])
                        if post_result.get("warnings"):
                            warnings.extend(post_result["warnings"])

                        metadata["functions_executed"].append(
                            {
                                "function": "post_process",
                                "success": False,
                                "errors": post_result["errors"],
                            }
                        )

                except Exception as e:
                    error_msg = f"Post-processing function failed: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error("Post-processing function failed", error=str(e))

                    metadata["functions_executed"].append(
                        {"function": "post_process", "success": False, "error": str(e)}
                    )

            processing_time = (time.time() - start_time) * 1000
            self.metrics["total_processing_time_ms"] += processing_time

            if not errors:
                self.metrics["transformations_success"] += 1
                return TransformationResult(
                    success=True,
                    data=current_data,
                    warnings=warnings,
                    metadata=metadata,
                    processing_time_ms=processing_time,
                )
            else:
                self.metrics["transformations_failed"] += 1
                return TransformationResult(
                    success=False,
                    data=current_data,
                    errors=errors,
                    warnings=warnings,
                    metadata=metadata,
                    processing_time_ms=processing_time,
                )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self.metrics["transformations_failed"] += 1
            self.metrics["total_processing_time_ms"] += processing_time

            error_msg = f"Custom transformation failed: {str(e)}"
            self.logger.error("Custom transformation failed", error=str(e))

            return TransformationResult(
                success=False,
                data=data,
                errors=[error_msg],
                processing_time_ms=processing_time,
            )

    def _execute_function(
        self, func: Callable, data: dict[str, Any], function_name: str
    ) -> dict[str, Any]:
        """Execute a custom function with proper error handling."""
        func_start_time = time.time()

        try:
            # Prepare function arguments
            kwargs = {
                "data": data.copy(),
                "context": self.function_context.copy(),
                "logger": self.logger,
                "transformer_name": self.name,
            }

            # Check function signature to determine what arguments to pass
            import inspect

            sig = inspect.signature(func)
            params = list(sig.parameters.keys())

            # Only pass parameters that the function expects
            func_kwargs = {k: v for k, v in kwargs.items() if k in params}

            # Execute the function
            result = func(**func_kwargs)

            # Handle different return types
            if isinstance(result, dict):
                # Function returned a dictionary with result information
                if "success" in result:
                    # Add execution time if not present
                    if "execution_time_ms" not in result:
                        result["execution_time_ms"] = (
                            time.time() - func_start_time
                        ) * 1000
                    return result
                else:
                    # Assume success if no explicit success flag
                    return {
                        "success": True,
                        "data": result,
                        "execution_time_ms": (time.time() - func_start_time) * 1000,
                    }
            else:
                # Function returned data directly
                return {
                    "success": True,
                    "data": result if result is not None else data,
                    "execution_time_ms": (time.time() - func_start_time) * 1000,
                }

        except Exception as e:
            # Try to use custom error handler if available
            if self.error_handler:
                try:
                    error_result = self.error_handler(
                        e, data, function_name, self.function_context
                    )
                    if isinstance(error_result, dict) and "success" in error_result:
                        # Ensure execution_time_ms is present
                        if "execution_time_ms" not in error_result:
                            error_result["execution_time_ms"] = (
                                time.time() - func_start_time
                            ) * 1000
                        return error_result
                    else:
                        return {
                            "success": False,
                            "data": data,
                            "errors": [f"Function {function_name} failed: {str(e)}"],
                            "execution_time_ms": (time.time() - func_start_time) * 1000,
                        }
                except Exception as handler_error:
                    self.logger.error(
                        "Error handler failed",
                        original_error=str(e),
                        handler_error=str(handler_error),
                    )

            # Default error handling
            return {
                "success": False,
                "data": data,
                "errors": [f"Function {function_name} failed: {str(e)}"],
                "execution_time_ms": (time.time() - func_start_time) * 1000,
            }

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

        # Check domain/entity conditions for Home Assistant events
        if "domain" in conditions:
            domain = conditions["domain"]
            if data.get("domain") != domain:
                return False

        if "entity_id" in conditions:
            entity_id = conditions["entity_id"]
            if data.get("entity_id") != entity_id:
                return False

        # Check custom condition function if provided
        if "custom_condition" in conditions and callable(
            conditions["custom_condition"]
        ):
            try:
                result = conditions["custom_condition"](data, self.function_context)
                if isinstance(result, bool):
                    return result
                else:
                    self.logger.warning(
                        "Custom condition function returned non-boolean value",
                        result=result,
                    )
                    return False
            except Exception as e:
                self.logger.warning("Custom condition function failed", error=str(e))
                return False

        return True

    def set_transform_function(self, func: Callable) -> None:
        """Set the main transformation function."""
        if not callable(func):
            raise ValueError("Function must be callable")

        self.transform_function = func
        self.logger.info("Set transformation function", function_name=func.__name__)

    def set_pre_process_function(self, func: Callable) -> None:
        """Set the pre-processing function."""
        if not callable(func):
            raise ValueError("Function must be callable")

        self.pre_process_function = func
        self.logger.info("Set pre-processing function", function_name=func.__name__)

    def set_post_process_function(self, func: Callable) -> None:
        """Set the post-processing function."""
        if not callable(func):
            raise ValueError("Function must be callable")

        self.post_process_function = func
        self.logger.info("Set post-processing function", function_name=func.__name__)

    def set_error_handler(self, func: Callable) -> None:
        """Set the error handler function."""
        if not callable(func):
            raise ValueError("Function must be callable")

        self.error_handler = func
        self.logger.info("Set error handler function", function_name=func.__name__)

    def update_context(self, context: dict[str, Any]) -> None:
        """Update the function context."""
        self.function_context.update(context)
        self.logger.debug("Updated function context", context_keys=list(context.keys()))

    def get_context(self) -> dict[str, Any]:
        """Get the current function context."""
        return self.function_context.copy()

"""Enhanced logging utilities for Home Assistant Activity Ingestor."""

import logging
import os
import sys
import uuid
from collections.abc import Callable
from contextvars import ContextVar
from datetime import datetime
from typing import Any

import structlog
from structlog.stdlib import LoggerFactory

from ..config import get_settings

# Context variable for correlation ID
_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)

# Context variable for additional context
_log_context: ContextVar[dict[str, Any]] = ContextVar("log_context", default={})


def setup_logging(
    log_level: str | None = None,
    log_format: str | None = None,
    log_file: str | None = None,
    service_name: str | None = None,
    log_rotation: dict[str, Any] | None = None,
) -> None:
    """Set up enhanced structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format (json, console)
        log_file: Log file path (if None, logs to console)
        service_name: Service name for log context
        log_rotation: Log rotation configuration
    """
    # Get configuration if not provided
    if log_level is None or log_format is None or service_name is None:
        try:
            config = get_settings()
            log_level = log_level or config.log_level
            log_format = log_format or config.log_format
            service_name = service_name or config.service_name
            log_rotation = log_rotation or getattr(config, "log_rotation", None)
        except Exception:
            # Fallback to defaults if configuration fails
            log_level = log_level or "INFO"
            log_format = log_format or "console"
            service_name = service_name or "ha-ingestor"
            log_rotation = log_rotation or {}

    # Convert log level string to integer
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure structlog with enhanced processors
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            _add_correlation_id,  # type: ignore[list-item]
            _add_log_context,  # type: ignore[list-item]
            _add_service_context(service_name),  # type: ignore[list-item]
            _add_environment_info,  # type: ignore[list-item]
            _get_renderer(log_format),
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    if log_file:
        # Set up log rotation if configured
        if log_rotation:
            from logging.handlers import RotatingFileHandler

            handler = RotatingFileHandler(
                log_file,
                maxBytes=log_rotation.get(
                    "max_bytes", 10 * 1024 * 1024
                ),  # 10MB default
                backupCount=log_rotation.get("backup_count", 5),
                encoding="utf-8",
            )
            logging.basicConfig(
                format="%(message)s",
                handlers=[handler],
                level=numeric_level,
            )
        else:
            logging.basicConfig(
                format="%(message)s",
                filename=log_file,
                level=numeric_level,
                encoding="utf-8",
            )
    else:
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=numeric_level,
        )

    # Set root logger level
    logging.getLogger().setLevel(numeric_level)

    # Log the setup
    logger = get_logger(__name__)
    logger.info(
        "Enhanced logging system initialized",
        log_level=log_level,
        log_format=log_format,
        log_file=log_file,
        service_name=service_name,
        log_rotation=log_rotation,
        correlation_id=_generate_correlation_id(),
    )


def _add_correlation_id(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add correlation ID to log records."""
    correlation_id = _correlation_id.get()
    if correlation_id:
        event_dict["correlation_id"] = correlation_id
    return event_dict


def _add_log_context(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add additional log context to log records."""
    context = _log_context.get()
    if context:
        event_dict.update(context)
    return event_dict


def _add_service_context(
    service_name: str,
) -> Callable[[Any, str, dict[str, Any]], dict[str, Any]]:
    """Add service context to log records."""

    def processor(
        logger: Any, method_name: str, event_dict: dict[str, Any]
    ) -> dict[str, Any]:
        event_dict["service"] = service_name
        return event_dict

    return processor


def _add_environment_info(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> Any:
    """Add environment information to log records."""
    event_dict["environment"] = os.getenv("ENVIRONMENT", "development")
    event_dict["hostname"] = os.getenv("HOSTNAME", "unknown")
    return event_dict


def _get_renderer(
    log_format: str,
) -> structlog.processors.JSONRenderer | structlog.dev.ConsoleRenderer:
    """Get the appropriate log renderer based on format."""
    if log_format.lower() == "json":
        return structlog.processors.JSONRenderer()
    else:
        return structlog.dev.ConsoleRenderer(colors=True)


def _generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid.uuid4())


def set_correlation_id(correlation_id: str | None = None) -> str:
    """Set correlation ID for current context.

    Args:
        correlation_id: Correlation ID to set. If None, generates a new one.

    Returns:
        The correlation ID that was set
    """
    if correlation_id is None:
        correlation_id = _generate_correlation_id()
    _correlation_id.set(correlation_id)
    return correlation_id


def get_correlation_id() -> str | None:
    """Get current correlation ID."""
    return _correlation_id.get()


def add_log_context(**kwargs: Any) -> None:
    """Add context to logs for current execution context.

    Args:
        **kwargs: Key-value pairs to add to log context
    """
    current_context = _log_context.get()
    current_context.update(kwargs)
    _log_context.set(current_context)


def clear_log_context() -> None:
    """Clear current log context."""
    _log_context.set({})


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance with enhanced context.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured structured logger with context
    """
    return structlog.get_logger(name)  # type: ignore[no-any-return]


def log_function_call(
    func_name: str, include_args: bool = True, include_result: bool = False
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Enhanced decorator to log function calls with parameters and context.

    Args:
        func_name: Name of the function being called
        include_args: Whether to include function arguments in logs
        include_result: Whether to include function result in logs
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **func_kwargs: Any) -> Any:
            logger = get_logger(func.__module__)
            correlation_id = get_correlation_id()

            # Log function entry
            log_data: dict[str, Any] = {
                "function": func_name,
                "correlation_id": correlation_id,
                "args_count": len(args),
            }

            if include_args and func_kwargs:
                log_data["parameters"] = func_kwargs

            logger.debug(f"Calling {func_name}", **log_data)

            start_time = datetime.utcnow()

            try:
                result = func(*args, **func_kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds()

                # Log successful completion
                completion_data = {
                    "function": func_name,
                    "correlation_id": correlation_id,
                    "duration_ms": round(duration * 1000, 2),
                }

                if include_result:
                    completion_data["result"] = str(result)[
                        :200
                    ]  # Truncate long results

                logger.debug(f"{func_name} completed successfully", **completion_data)
                return result

            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()

                # Log error with enhanced context
                error_data = {
                    "function": func_name,
                    "correlation_id": correlation_id,
                    "duration_ms": round(duration * 1000, 2),
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "exc_info": True,
                }

                logger.error(f"{func_name} failed", **error_data)
                raise

        return wrapper

    return decorator


def log_performance(
    operation: str, log_level: str = "DEBUG"
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Enhanced decorator to log operation performance with context.

    Args:
        operation: Description of the operation being timed
        log_level: Log level for performance logs
    """
    import time

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_logger(func.__module__)
            correlation_id = get_correlation_id()
            start_time = time.time()

            # Log operation start
            logger.log(
                getattr(logging, log_level.upper()),
                f"{operation} started",
                operation=operation,
                correlation_id=correlation_id,
            )

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Log successful completion
                logger.log(
                    getattr(logging, log_level.upper()),
                    f"{operation} completed",
                    operation=operation,
                    correlation_id=correlation_id,
                    duration_ms=round(duration * 1000, 2),
                )
                return result

            except Exception as e:
                duration = time.time() - start_time

                # Log error with context
                logger.error(
                    f"{operation} failed",
                    operation=operation,
                    correlation_id=correlation_id,
                    duration_ms=round(duration * 1000, 2),
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise

        return wrapper

    return decorator


def setup_default_logging() -> None:
    """Set up enhanced logging with default configuration from settings."""
    try:
        config = get_settings()

        # Get log rotation settings if available
        log_rotation = None
        if hasattr(config, "log_rotation"):
            log_rotation = config.log_rotation
        elif hasattr(config, "log_max_size") or hasattr(config, "log_backup_count"):
            log_rotation = {
                "max_bytes": getattr(config, "log_max_size", 10 * 1024 * 1024),
                "backup_count": getattr(config, "log_backup_count", 5),
            }

        setup_logging(
            log_level=config.log_level,
            log_format=config.log_format,
            log_file=config.log_file,
            service_name=config.service_name,
            log_rotation=log_rotation,
        )
    except Exception as e:
        # Fallback to basic logging if configuration fails
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        logging.error(f"Failed to setup enhanced logging: {e}")
        logging.info("Falling back to basic logging")


def get_logger_for_module(module_name: str) -> structlog.stdlib.BoundLogger:
    """Get a logger for a specific module with enhanced context.

    Args:
        module_name: Module name (e.g., 'ha_ingestor.mqtt')

    Returns:
        Configured structured logger for the module
    """
    return get_logger(module_name)


def log_with_context(
    logger: structlog.stdlib.BoundLogger, message: str, **kwargs: Any
) -> None:
    """Log a message with current context automatically added.

    Args:
        logger: Logger instance to use
        message: Message to log
        **kwargs: Additional key-value pairs to log
    """
    # Add current context
    context = _log_context.get()
    correlation_id = _correlation_id.get()

    if context:
        kwargs.update(context)
    if correlation_id:
        kwargs["correlation_id"] = correlation_id

    logger.info(message, **kwargs)


class LogContextManager:
    """Context manager for temporary log context."""

    def __init__(self, **kwargs: Any) -> None:
        self.context = kwargs
        self.previous_context: dict[str, Any] = {}

    def __enter__(self) -> "LogContextManager":
        self.previous_context = _log_context.get()
        new_context = self.previous_context.copy()
        new_context.update(self.context)
        _log_context.set(new_context)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        _log_context.set(self.previous_context)


# Convenience function for quick context logging
def log_context(**kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to add context to all logs within a function."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **func_kwargs: Any) -> Any:
            with LogContextManager(**kwargs):
                return func(*args, **func_kwargs)

        return wrapper

    return decorator

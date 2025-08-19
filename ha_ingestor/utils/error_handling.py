"""Comprehensive error handling and recovery utilities."""

import asyncio
import traceback
from typing import Any, Callable, Dict, List, Optional, Type, Union
from enum import Enum
from datetime import datetime, timedelta

from .logging import get_logger

logger = get_logger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    CONNECTION = "connection"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    VALIDATION = "validation"
    RESOURCE = "resource"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class ErrorContext:
    """Context information for error handling."""
    
    def __init__(
        self,
        operation: str,
        component: str,
        timestamp: Optional[datetime] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """Initialize error context.
        
        Args:
            operation: Name of the operation that failed
            component: Component where the error occurred
            timestamp: When the error occurred
            user_id: User ID if applicable
            session_id: Session ID if applicable
            request_id: Request ID if applicable
            additional_data: Additional context data
        """
        self.operation = operation
        self.component = component
        self.timestamp = timestamp or datetime.utcnow()
        self.user_id = user_id
        self.session_id = session_id
        self.request_id = request_id
        self.additional_data = additional_data or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "operation": self.operation,
            "component": self.component,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "additional_data": self.additional_data
        }


class ErrorInfo:
    """Detailed error information."""
    
    def __init__(
        self,
        exception: Exception,
        context: ErrorContext,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        recoverable: bool = True,
        retry_count: int = 0,
        max_retries: int = 3
    ):
        """Initialize error information.
        
        Args:
            exception: The exception that occurred
            context: Error context information
            severity: Error severity level
            category: Error category
            recoverable: Whether the error is recoverable
            retry_count: Current retry attempt
            max_retries: Maximum retry attempts
        """
        self.exception = exception
        self.context = context
        self.severity = severity
        self.category = category
        self.recoverable = recoverable
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.traceback = traceback.format_exc()
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error info to dictionary."""
        return {
            "exception_type": type(self.exception).__name__,
            "exception_message": str(self.exception),
            "context": self.context.to_dict(),
            "severity": self.severity.value,
            "category": self.category.value,
            "recoverable": self.recoverable,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "traceback": self.traceback,
            "timestamp": self.timestamp.isoformat()
        }
    
    def should_retry(self) -> bool:
        """Check if error should be retried."""
        return (
            self.recoverable and 
            self.retry_count < self.max_retries and
            self.severity != ErrorSeverity.CRITICAL
        )


class ErrorClassifier:
    """Classifies errors based on exception type and context."""
    
    # Mapping of exception types to error categories and severity
    EXCEPTION_MAPPING = {
        ConnectionError: (ErrorCategory.CONNECTION, ErrorSeverity.MEDIUM),
        TimeoutError: (ErrorCategory.TIMEOUT, ErrorSeverity.MEDIUM),
        OSError: (ErrorCategory.SYSTEM, ErrorSeverity.MEDIUM),
        ValueError: (ErrorCategory.VALIDATION, ErrorSeverity.LOW),
        KeyError: (ErrorCategory.VALIDATION, ErrorSeverity.LOW),
        TypeError: (ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM),
        PermissionError: (ErrorCategory.AUTHORIZATION, ErrorSeverity.HIGH),
        FileNotFoundError: (ErrorCategory.RESOURCE, ErrorSeverity.MEDIUM),
        MemoryError: (ErrorCategory.SYSTEM, ErrorSeverity.CRITICAL),
        KeyboardInterrupt: (ErrorCategory.SYSTEM, ErrorSeverity.LOW),
    }
    
    @classmethod
    def classify_error(
        cls,
        exception: Exception,
        context: ErrorContext
    ) -> tuple[ErrorCategory, ErrorSeverity]:
        """Classify an error based on exception type and context.
        
        Args:
            exception: The exception to classify
            context: Error context information
            
        Returns:
            Tuple of (category, severity)
        """
        # Check if we have a direct mapping for this exception type
        exception_type = type(exception)
        if exception_type in cls.EXCEPTION_MAPPING:
            return cls.EXCEPTION_MAPPING[exception_type]
        
        # Check for specific error messages that indicate certain categories
        error_message = str(exception).lower()
        
        if "rate limit" in error_message or "too many requests" in error_message:
            return ErrorCategory.RATE_LIMIT, ErrorSeverity.MEDIUM
        
        if "authentication" in error_message or "unauthorized" in error_message:
            return ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH
        
        if "timeout" in error_message or "timed out" in error_message:
            return ErrorCategory.TIMEOUT, ErrorSeverity.MEDIUM
        
        if "connection" in error_message or "network" in error_message:
            return ErrorCategory.CONNECTION, ErrorSeverity.MEDIUM
        
        # Default classification
        return ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM


class ErrorRecoveryStrategy:
    """Implements automatic error recovery strategies."""
    
    def __init__(self):
        """Initialize error recovery strategy."""
        self.logger = get_logger(__name__)
        self.recovery_attempts: Dict[str, int] = {}
        self.last_recovery_time: Dict[str, datetime] = {}
    
    async def attempt_recovery(
        self,
        error_info: ErrorInfo,
        recovery_func: Optional[Callable] = None,
        recovery_args: tuple = (),
        recovery_kwargs: dict = None
    ) -> bool:
        """Attempt to recover from an error.
        
        Args:
            error_info: Information about the error
            recovery_func: Function to call for recovery
            recovery_args: Arguments for recovery function
            recovery_kwargs: Keyword arguments for recovery function
            
        Returns:
            True if recovery successful, False otherwise
        """
        if not error_info.should_retry():
            self.logger.warning("Error not recoverable, skipping recovery",
                               error_type=type(error_info.exception).__name__,
                               severity=error_info.severity.value)
            return False
        
        recovery_key = f"{error_info.context.component}:{error_info.context.operation}"
        
        # Check if we've tried too many times recently
        if self._should_skip_recovery(recovery_key):
            self.logger.info("Skipping recovery due to recent attempts",
                            recovery_key=recovery_key)
            return False
        
        self.logger.info("Attempting error recovery",
                         error_type=type(error_info.exception).__name__,
                         recovery_key=recovery_key,
                         retry_count=error_info.retry_count)
        
        try:
            if recovery_func:
                if asyncio.iscoroutinefunction(recovery_func):
                    result = await recovery_func(*recovery_args, **recovery_kwargs or {})
                else:
                    result = recovery_func(*recovery_args, **recovery_kwargs or {})
                
                if result:
                    self.logger.info("Error recovery successful",
                                    recovery_key=recovery_key)
                    self._record_successful_recovery(recovery_key)
                    return True
                else:
                    self.logger.warning("Error recovery failed",
                                       recovery_key=recovery_key)
                    self._record_failed_recovery(recovery_key)
                    return False
            else:
                # Default recovery strategies based on error category
                return await self._default_recovery(error_info)
                
        except Exception as e:
            self.logger.error("Error during recovery attempt",
                             recovery_key=recovery_key,
                             error=str(e))
            self._record_failed_recovery(recovery_key)
            return False
    
    async def _default_recovery(self, error_info: ErrorInfo) -> bool:
        """Default recovery strategies based on error category.
        
        Args:
            error_info: Information about the error
            
        Returns:
            True if recovery successful, False otherwise
        """
        if error_info.category == ErrorCategory.CONNECTION:
            # Wait and retry for connection errors
            await asyncio.sleep(1.0)
            return True
        
        elif error_info.category == ErrorCategory.RATE_LIMIT:
            # Wait longer for rate limit errors
            await asyncio.sleep(5.0)
            return True
        
        elif error_info.category == ErrorCategory.TIMEOUT:
            # Wait and retry for timeout errors
            await asyncio.sleep(2.0)
            return True
        
        elif error_info.category == ErrorCategory.AUTHENTICATION:
            # Authentication errors usually require manual intervention
            self.logger.error("Authentication error requires manual intervention")
            return False
        
        elif error_info.category == ErrorCategory.AUTHORIZATION:
            # Authorization errors usually require manual intervention
            self.logger.error("Authorization error requires manual intervention")
            return False
        
        # Default: wait a bit and retry
        await asyncio.sleep(1.0)
        return True
    
    def _should_skip_recovery(self, recovery_key: str) -> bool:
        """Check if recovery should be skipped due to recent attempts.
        
        Args:
            recovery_key: Key identifying the recovery operation
            
        Returns:
            True if recovery should be skipped
        """
        if recovery_key not in self.last_recovery_time:
            return False
        
        last_attempt = self.last_recovery_time[recovery_key]
        time_since_last = datetime.utcnow() - last_attempt
        
        # Skip if last attempt was less than 30 seconds ago
        return time_since_last < timedelta(seconds=30)
    
    def _record_successful_recovery(self, recovery_key: str) -> None:
        """Record successful recovery attempt."""
        self.recovery_attempts[recovery_key] = self.recovery_attempts.get(recovery_key, 0) + 1
        self.last_recovery_time[recovery_key] = datetime.utcnow()
    
    def _record_failed_recovery(self, recovery_key: str) -> None:
        """Record failed recovery attempt."""
        self.recovery_attempts[recovery_key] = self.recovery_attempts.get(recovery_key, 0) + 1
        self.last_recovery_time[recovery_key] = datetime.utcnow()


class ErrorHandler:
    """Main error handler that coordinates error classification and recovery."""
    
    def __init__(self):
        """Initialize error handler."""
        self.logger = get_logger(__name__)
        self.classifier = ErrorClassifier()
        self.recovery_strategy = ErrorRecoveryStrategy()
        self.error_history: List[ErrorInfo] = []
        self.max_history_size = 1000
    
    def handle_error(
        self,
        exception: Exception,
        context: ErrorContext,
        retry_count: int = 0,
        max_retries: int = 3
    ) -> ErrorInfo:
        """Handle an error by classifying it and creating error info.
        
        Args:
            exception: The exception that occurred
            context: Error context information
            retry_count: Current retry attempt
            max_retries: Maximum retry attempts
            
        Returns:
            ErrorInfo object with classification and recovery information
        """
        # Classify the error
        category, severity = self.classifier.classify_error(exception, context)
        
        # Determine if error is recoverable
        recoverable = self._is_error_recoverable(category, severity)
        
        # Create error info
        error_info = ErrorInfo(
            exception=exception,
            context=context,
            severity=severity,
            category=category,
            recoverable=recoverable,
            retry_count=retry_count,
            max_retries=max_retries
        )
        
        # Log the error
        self._log_error(error_info)
        
        # Store in history
        self._store_error(error_info)
        
        return error_info
    
    async def handle_error_with_recovery(
        self,
        exception: Exception,
        context: ErrorContext,
        recovery_func: Optional[Callable] = None,
        recovery_args: tuple = (),
        recovery_kwargs: dict = None,
        retry_count: int = 0,
        max_retries: int = 3
    ) -> tuple[ErrorInfo, bool]:
        """Handle an error and attempt recovery.
        
        Args:
            exception: The exception that occurred
            context: Error context information
            recovery_func: Function to call for recovery
            recovery_args: Arguments for recovery function
            recovery_kwargs: Keyword arguments for recovery function
            retry_count: Current retry attempt
            max_retries: Maximum retry attempts
            
        Returns:
            Tuple of (ErrorInfo, recovery_success)
        """
        # Handle the error
        error_info = self.handle_error(exception, context, retry_count, max_retries)
        
        # Attempt recovery if appropriate
        if error_info.should_retry():
            recovery_success = await self.recovery_strategy.attempt_recovery(
                error_info, recovery_func, recovery_args, recovery_kwargs or {}
            )
            return error_info, recovery_success
        
        return error_info, False
    
    def _is_error_recoverable(self, category: ErrorCategory, severity: ErrorSeverity) -> bool:
        """Determine if an error is recoverable based on category and severity.
        
        Args:
            category: Error category
            severity: Error severity
            
        Returns:
            True if error is recoverable
        """
        # Critical errors are never recoverable
        if severity == ErrorSeverity.CRITICAL:
            return False
        
        # Authentication and authorization errors usually require manual intervention
        if category in (ErrorCategory.AUTHENTICATION, ErrorCategory.AUTHORIZATION):
            return False
        
        # Most other errors are recoverable
        return True
    
    def _log_error(self, error_info: ErrorInfo) -> None:
        """Log error information with appropriate log level."""
        log_data = {
            "error_type": type(error_info.exception).__name__,
            "error_message": str(error_info.exception),
            "component": error_info.context.component,
            "operation": error_info.context.operation,
            "category": error_info.category.value,
            "severity": error_info.severity.value,
            "recoverable": error_info.recoverable,
            "retry_count": error_info.retry_count
        }
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            self.logger.critical("Critical error occurred", **log_data)
        elif error_info.severity == ErrorSeverity.HIGH:
            self.logger.error("High severity error occurred", **log_data)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            self.logger.warning("Medium severity error occurred", **log_data)
        else:
            self.logger.info("Low severity error occurred", **log_data)
    
    def _store_error(self, error_info: ErrorInfo) -> None:
        """Store error in history, maintaining max size."""
        self.error_history.append(error_info)
        
        # Remove old errors if we exceed max history size
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of error history."""
        if not self.error_history:
            return {"total_errors": 0}
        
        # Count errors by category and severity
        category_counts = {}
        severity_counts = {}
        recoverable_count = 0
        
        for error in self.error_history:
            category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
            severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
            if error.recoverable:
                recoverable_count += 1
        
        return {
            "total_errors": len(self.error_history),
            "recoverable_errors": recoverable_count,
            "unrecoverable_errors": len(self.error_history) - recoverable_count,
            "category_breakdown": category_counts,
            "severity_breakdown": severity_counts,
            "recent_errors": [
                error.to_dict() for error in self.error_history[-10:]
            ]
        }


# Global error handler instance
error_handler = ErrorHandler()


def handle_error_decorator(
    context_operation: str,
    context_component: str,
    max_retries: int = 3,
    recovery_func: Optional[Callable] = None
):
    """Decorator to automatically handle errors in functions.
    
    Args:
        context_operation: Operation name for error context
        context_component: Component name for error context
        max_retries: Maximum retry attempts
        recovery_func: Function to call for recovery
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args, **kwargs):
            retry_count = 0
            
            while retry_count <= max_retries:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    # Create error context
                    context = ErrorContext(
                        operation=context_operation,
                        component=context_component,
                        additional_data={
                            "function": func.__name__,
                            "args": str(args),
                            "kwargs": str(kwargs)
                        }
                    )
                    
                    # Handle error with recovery
                    error_info, recovery_success = await error_handler.handle_error_with_recovery(
                        e, context, recovery_func, (), {}, retry_count, max_retries
                    )
                    
                    if not error_info.should_retry() or not recovery_success:
                        raise e
                    
                    retry_count += 1
            
            # If we get here, all retries failed
            raise Exception(f"Function {func.__name__} failed after {max_retries} retries")
        
        def sync_wrapper(*args, **kwargs):
            retry_count = 0
            
            while retry_count <= max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Create error context
                    context = ErrorContext(
                        operation=context_operation,
                        component=context_component,
                        additional_data={
                            "function": func.__name__,
                            "args": str(args),
                            "kwargs": str(kwargs)
                        }
                    )
                    
                    # Handle error
                    error_info = error_handler.handle_error(e, context, retry_count, max_retries)
                    
                    if not error_info.should_retry():
                        raise e
                    
                    retry_count += 1
            
            # If we get here, all retries failed
            raise Exception(f"Function {func.__name__} failed after {max_retries} retries")
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

"""
Correlation ID Middleware for Request Tracking Across Services
"""

import time
import uuid
from typing import Optional, Callable, Any
from contextvars import ContextVar
from functools import wraps

from .logging_config import correlation_id, generate_correlation_id, set_correlation_id, get_correlation_id


class CorrelationMiddleware:
    """Middleware for handling correlation IDs in web frameworks"""
    
    def __init__(self, app=None, header_name: str = 'X-Correlation-ID'):
        self.app = app
        self.header_name = header_name
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the middleware with the app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Set up correlation ID before request processing"""
        from flask import request
        
        # Get correlation ID from header or generate new one
        corr_id = request.headers.get(self.header_name)
        if not corr_id:
            corr_id = generate_correlation_id()
        
        # Set in context
        set_correlation_id(corr_id)
        
        # Add to request context for later use
        request.correlation_id = corr_id
    
    def after_request(self, response):
        """Add correlation ID to response headers"""
        corr_id = get_correlation_id()
        if corr_id:
            response.headers[self.header_name] = corr_id
        return response


def correlation_context(corr_id: Optional[str] = None):
    """Context manager for correlation ID handling"""
    class CorrelationContext:
        def __init__(self, correlation_id: Optional[str] = None):
            self.correlation_id = correlation_id or generate_correlation_id()
            self.old_correlation_id = None
        
        def __enter__(self):
            self.old_correlation_id = get_correlation_id()
            set_correlation_id(self.correlation_id)
            return self.correlation_id
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.old_correlation_id:
                set_correlation_id(self.old_correlation_id)
            else:
                correlation_id.set(None)
    
    return CorrelationContext(corr_id)


def with_correlation_id(corr_id: Optional[str] = None):
    """Decorator to add correlation ID to function execution"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            with correlation_context(corr_id):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def propagate_correlation_id(headers: dict, header_name: str = 'X-Correlation-ID') -> dict:
    """Add correlation ID to headers for service-to-service communication"""
    corr_id = get_correlation_id()
    if corr_id:
        headers[header_name] = corr_id
    return headers


def extract_correlation_id(headers: dict, header_name: str = 'X-Correlation-ID') -> Optional[str]:
    """Extract correlation ID from headers"""
    return headers.get(header_name)


class FastAPICorrelationMiddleware:
    """Correlation ID middleware for FastAPI"""
    
    def __init__(self, header_name: str = 'X-Correlation-ID'):
        self.header_name = header_name
    
    async def __call__(self, request, call_next):
        """Process request with correlation ID"""
        # Get correlation ID from header or generate new one
        corr_id = request.headers.get(self.header_name)
        if not corr_id:
            corr_id = generate_correlation_id()
        
        # Set in context
        set_correlation_id(corr_id)
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers[self.header_name] = corr_id
        
        return response


class AioHTTPCorrelationMiddleware:
    """Correlation ID middleware for aiohttp"""
    
    def __init__(self, header_name: str = 'X-Correlation-ID'):
        self.header_name = header_name
    
    async def __call__(self, request, handler):
        """Process request with correlation ID"""
        # Get correlation ID from header or generate new one
        corr_id = request.headers.get(self.header_name)
        if not corr_id:
            corr_id = generate_correlation_id()
        
        # Set in context
        set_correlation_id(corr_id)
        
        # Process request
        response = await handler(request)
        
        # Add correlation ID to response headers
        response.headers[self.header_name] = corr_id
        
        return response


def create_correlation_context(corr_id: Optional[str] = None) -> dict:
    """Create a context dictionary with correlation ID for async operations"""
    correlation_id_value = corr_id or generate_correlation_id()
    return {
        'correlation_id': correlation_id_value,
        'start_time': time.time()
    }


def update_correlation_context(context: dict, **updates) -> dict:
    """Update correlation context with additional information"""
    context.update(updates)
    return context


def get_correlation_context() -> dict:
    """Get current correlation context"""
    return {
        'correlation_id': get_correlation_id(),
        'timestamp': time.time()
    }

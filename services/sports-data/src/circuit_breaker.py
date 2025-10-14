"""
Simple Circuit Breaker for InfluxDB Writer

Prevents cascading failures by blocking writes after consecutive failures.
Story 12.1 - InfluxDB Persistence Layer
"""

import logging
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Simple circuit breaker for InfluxDB operations.
    
    - Tracks consecutive failures
    - Opens circuit after threshold failures (blocks writes)
    - Auto-recovers after timeout
    """
    
    def __init__(self, failure_threshold: int = 3, timeout_seconds: int = 60):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Consecutive failures before opening circuit
            timeout_seconds: Seconds to wait before allowing retry
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time = None
        self.is_circuit_open = False
    
    def record_success(self):
        """Record successful operation - reset failures"""
        self.failure_count = 0
        self.is_circuit_open = False
    
    def record_failure(self):
        """Record failed operation - may open circuit"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.is_circuit_open = True
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def is_open(self) -> bool:
        """Check if circuit is open (blocking writes)"""
        if not self.is_circuit_open:
            return False
        
        # Auto-recover after timeout
        if self.last_failure_time:
            elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
            if elapsed >= self.timeout_seconds:
                logger.info("Circuit breaker timeout elapsed, allowing retry")
                self.is_circuit_open = False
                self.failure_count = 0
                return False
        
        return True
    
    def get_status(self) -> str:
        """Get status: 'open' or 'closed'"""
        return 'open' if self.is_open() else 'closed'


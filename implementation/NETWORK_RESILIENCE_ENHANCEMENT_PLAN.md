# Network Resilience Enhancement Plan
## Home Assistant Ingestor - Infinite Retry with Graceful Degradation

**Created:** October 14, 2025  
**Author:** BMad Master  
**Priority:** HIGH - Critical for production reliability

---

## Problem Statement

### Current Behavior (ISSUE)

The WebSocket ingestion service **permanently stops** after exhausting retry attempts when:
- Internet connection is down at startup
- Home Assistant is unreachable
- Network is temporarily unavailable

**Current Retry Logic:**
```python
# connection_manager.py (Line 40)
self.max_retries = 10  # ❌ Gives up after 10 attempts

# _reconnect_loop() (Line 208-210)
if self.current_retry_count >= self.max_retries:
    logger.error(f"Maximum reconnection attempts ({self.max_retries}) reached")
    self.is_running = False  # ❌ STOPS PERMANENTLY
```

**Impact:**
- ✅ Service container stays "healthy" (passes Docker health check)
- 🔴 Connection manager stops running (`is_running = False`)
- 🔴 No automatic recovery when network returns
- 🔴 Manual container restart required
- 🔴 Data loss during downtime
- 🔴 Poor user experience

---

## Proposed Solution

### Overview: Infinite Retry with Intelligent Backoff

Replace fixed retry limit with **infinite retry** strategy that includes:
1. **Never give up** - continuous retry attempts
2. **Smart backoff** - exponential backoff with maximum ceiling
3. **Health states** - distinguish "waiting" from "failed"
4. **Circuit breaker** - detect persistent failures and adjust strategy
5. **Monitoring** - detailed metrics and alerts
6. **Configurability** - environment-based retry parameters

### Design Principles

1. **Resilience First:** Service should always attempt to recover
2. **Resource Efficient:** Don't hammer the network with rapid retries
3. **Observability:** Clear visibility into retry state and behavior
4. **Configurability:** Operators can tune retry behavior
5. **Graceful Degradation:** Service remains operational in degraded mode

---

## Detailed Implementation Plan

### Phase 1: Enhanced Retry Logic (Core Enhancement)

#### 1.1 Infinite Retry with Backoff Stages

Replace fixed `max_retries` with **staged retry strategy**:

```python
class RetryStrategy:
    """Multi-stage retry strategy for network resilience"""
    
    STAGES = {
        "rapid": {
            "attempts": 10,
            "base_delay": 1,      # 1s
            "max_delay": 5,       # 5s
            "backoff": 1.5,
            "description": "Quick retries for transient failures"
        },
        "moderate": {
            "attempts": 20,
            "base_delay": 5,      # 5s
            "max_delay": 30,      # 30s
            "backoff": 2,
            "description": "Medium-paced retries for temporary outages"
        },
        "persistent": {
            "attempts": -1,       # ♾️ INFINITE
            "base_delay": 30,     # 30s
            "max_delay": 300,     # 5 minutes
            "backoff": 2,
            "description": "Long-interval retries for extended outages"
        }
    }
```

**Benefits:**
- Fast recovery for brief network hiccups
- Resource-efficient for extended outages
- Never stops trying
- Predictable retry intervals

#### 1.2 Connection State Machine

Introduce proper state management:

```python
class ConnectionState(Enum):
    """Connection states for state machine"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    SUBSCRIBING = "subscribing"
    ACTIVE = "active"
    RETRYING_RAPID = "retrying_rapid"
    RETRYING_MODERATE = "retrying_moderate"
    RETRYING_PERSISTENT = "retrying_persistent"
    CIRCUIT_OPEN = "circuit_open"  # Circuit breaker activated
```

**State Transitions:**
```
DISCONNECTED
    ↓ (start)
CONNECTING → RETRYING_RAPID → RETRYING_MODERATE → RETRYING_PERSISTENT
    ↓ (success)                                            ↑
CONNECTED                                                  |
    ↓ (auth)                                              |
AUTHENTICATED                                              |
    ↓ (subscribe)                                         |
SUBSCRIBING                                               |
    ↓ (success)                                           |
ACTIVE ←→ (disconnect) ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ←┘
    ↓ (persistent failure)
CIRCUIT_OPEN (temporary pause, then back to RETRYING_RAPID)
```

#### 1.3 Circuit Breaker Pattern

Detect persistent failures and adjust behavior:

```python
class CircuitBreaker:
    """Circuit breaker for connection management"""
    
    def __init__(self):
        self.failure_threshold = 50      # Open circuit after 50 consecutive failures
        self.success_threshold = 3       # Close circuit after 3 consecutive successes
        self.timeout = 300               # 5 minutes in open state
        self.state = "closed"
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.last_failure_time = None
    
    async def call(self, func):
        """Execute function with circuit breaker protection"""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half_open"
            else:
                raise CircuitBreakerOpenError("Circuit breaker is open")
        
        try:
            result = await func()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
```

**Benefits:**
- Prevents resource exhaustion from endless rapid failures
- Allows system to "cool down" during persistent issues
- Automatic recovery testing after timeout period

---

### Phase 2: Enhanced Health Checks

#### 2.1 Detailed Health States

Replace binary "healthy/unhealthy" with rich health model:

```python
class HealthStatus(Enum):
    """Detailed health status for monitoring"""
    HEALTHY = "healthy"                    # Connected and receiving events
    DEGRADED = "degraded"                  # Connected but not receiving events
    WAITING = "waiting"                    # Retrying, expected to recover
    CIRCUIT_OPEN = "circuit_open"          # Circuit breaker activated
    UNHEALTHY = "unhealthy"                # Configuration or auth issues
    UNKNOWN = "unknown"                    # Initial state

class HealthDetail:
    """Detailed health information"""
    status: HealthStatus
    connection_state: ConnectionState
    retry_stage: str                       # "rapid", "moderate", "persistent"
    retry_attempt: int
    next_retry_in: float                   # seconds
    last_successful_connection: datetime
    time_since_last_event: float           # seconds
    consecutive_failures: int
    reason: str                            # Human-readable explanation
```

**Health Check Response Example:**
```json
{
  "status": "waiting",
  "connection_state": "retrying_moderate",
  "retry_stage": "moderate",
  "retry_attempt": 15,
  "next_retry_in": 23.4,
  "last_successful_connection": "2025-10-14T13:15:00Z",
  "time_since_last_event": 3245.6,
  "consecutive_failures": 15,
  "reason": "Unable to connect to Home Assistant at http://192.168.1.86:8123. Will retry in 23.4 seconds.",
  "service_operational": true,
  "degraded_mode": true,
  "recommendations": [
    "Check Home Assistant availability",
    "Verify network connectivity",
    "Review HOME_ASSISTANT_URL configuration"
  ]
}
```

#### 2.2 Smart Health Check

Distinguish between different failure types:

```python
def assess_health(self) -> HealthDetail:
    """Comprehensive health assessment"""
    
    # Connected and active
    if self.state == ConnectionState.ACTIVE:
        if self.time_since_last_event < 300:  # 5 minutes
            return HealthDetail(status=HealthStatus.HEALTHY, reason="Active")
        else:
            return HealthDetail(status=HealthStatus.DEGRADED, 
                              reason="Connected but no events received")
    
    # Retrying - expected to recover
    if self.state in [ConnectionState.RETRYING_RAPID, 
                      ConnectionState.RETRYING_MODERATE,
                      ConnectionState.RETRYING_PERSISTENT]:
        return HealthDetail(status=HealthStatus.WAITING,
                          reason=f"Retrying connection ({self.retry_stage})")
    
    # Circuit breaker activated
    if self.state == ConnectionState.CIRCUIT_OPEN:
        return HealthDetail(status=HealthStatus.CIRCUIT_OPEN,
                          reason="Too many failures, cooling down")
    
    # Configuration or authentication issues
    if self.last_error and "authentication" in self.last_error.lower():
        return HealthDetail(status=HealthStatus.UNHEALTHY,
                          reason="Authentication failed - check token")
    
    return HealthDetail(status=HealthStatus.UNKNOWN,
                       reason="Status unknown")
```

---

### Phase 3: Configuration & Monitoring

#### 3.1 Environment Configuration

Add configurable retry parameters:

```bash
# docker-compose.yml / .env
WEBSOCKET_RETRY_STRATEGY=infinite  # Options: "infinite", "limited", "aggressive"
WEBSOCKET_RETRY_RAPID_ATTEMPTS=10
WEBSOCKET_RETRY_RAPID_BASE_DELAY=1
WEBSOCKET_RETRY_RAPID_MAX_DELAY=5
WEBSOCKET_RETRY_MODERATE_ATTEMPTS=20
WEBSOCKET_RETRY_MODERATE_BASE_DELAY=5
WEBSOCKET_RETRY_MODERATE_MAX_DELAY=30
WEBSOCKET_RETRY_PERSISTENT_BASE_DELAY=30
WEBSOCKET_RETRY_PERSISTENT_MAX_DELAY=300
WEBSOCKET_CIRCUIT_BREAKER_ENABLED=true
WEBSOCKET_CIRCUIT_BREAKER_THRESHOLD=50
WEBSOCKET_CIRCUIT_BREAKER_TIMEOUT=300
WEBSOCKET_HEALTH_CHECK_TOLERANCE=300  # Consider degraded after 5min without events
```

**Preset Strategies:**
```python
RETRY_STRATEGIES = {
    "infinite": {
        "description": "Never give up, suitable for production",
        "rapid_attempts": 10,
        "moderate_attempts": 20,
        "persistent_attempts": -1,  # infinite
        "circuit_breaker": True
    },
    "aggressive": {
        "description": "Faster retries, higher resource usage",
        "rapid_attempts": 20,
        "moderate_attempts": 40,
        "persistent_attempts": -1,
        "circuit_breaker": False,
        "rapid_max_delay": 3,
        "moderate_max_delay": 15
    },
    "conservative": {
        "description": "Slower retries, lower resource usage",
        "rapid_attempts": 5,
        "moderate_attempts": 10,
        "persistent_attempts": -1,
        "circuit_breaker": True,
        "persistent_max_delay": 600  # 10 minutes
    },
    "limited": {
        "description": "Traditional fixed retry (legacy mode)",
        "rapid_attempts": 10,
        "moderate_attempts": 0,
        "persistent_attempts": 0,
        "max_total_retries": 10
    }
}
```

#### 3.2 Metrics & Monitoring

Add comprehensive metrics:

```python
class ConnectionMetrics:
    """Metrics for connection resilience monitoring"""
    
    # Counters
    total_connection_attempts: int
    successful_connections: int
    failed_connections: int
    authentication_failures: int
    network_errors: int
    timeout_errors: int
    
    # Gauges
    current_retry_stage: str
    current_retry_attempt: int
    consecutive_failures: int
    time_in_current_state: float  # seconds
    time_since_last_success: float
    
    # Histograms
    connection_duration_seconds: List[float]
    retry_delay_seconds: List[float]
    time_to_recovery: List[float]  # From failure to success
    
    # Rates
    connection_attempts_per_minute: float
    failures_per_minute: float
    recovery_success_rate: float
```

**Prometheus-style Metrics:**
```
# HELP websocket_connection_attempts_total Total connection attempts
# TYPE websocket_connection_attempts_total counter
websocket_connection_attempts_total 250

# HELP websocket_retry_stage Current retry stage
# TYPE websocket_retry_stage gauge
websocket_retry_stage{stage="persistent"} 1

# HELP websocket_time_since_last_success_seconds Time since last successful connection
# TYPE websocket_time_since_last_success_seconds gauge
websocket_time_since_last_success_seconds 3245.6

# HELP websocket_circuit_breaker_state Circuit breaker state (0=closed, 1=open, 2=half_open)
# TYPE websocket_circuit_breaker_state gauge
websocket_circuit_breaker_state 0
```

#### 3.3 Alerting Rules

Define alert thresholds:

```yaml
alerts:
  - name: WebSocketPersistentRetrying
    condition: retry_stage == "persistent" AND time_in_stage > 600
    severity: warning
    message: "WebSocket has been in persistent retry for >10 minutes"
    
  - name: WebSocketCircuitBreakerOpen
    condition: circuit_breaker_state == "open"
    severity: warning
    message: "Circuit breaker activated due to too many failures"
    
  - name: WebSocketExtendedOutage
    condition: time_since_last_success > 3600
    severity: critical
    message: "No successful connection for >1 hour"
    
  - name: WebSocketAuthenticationFailure
    condition: authentication_failures > 0
    severity: critical
    message: "Authentication failures detected - check token"
    
  - name: WebSocketDegraded
    condition: status == "degraded" AND time_since_last_event > 600
    severity: warning
    message: "Connected but no events received for >10 minutes"
```

---

### Phase 4: Testing Strategy

#### 4.1 Resilience Test Scenarios

```python
# tests/resilience/test_network_resilience.py

class TestNetworkResilience:
    """Test network resilience scenarios"""
    
    async def test_startup_without_network(self):
        """Service starts successfully even without network"""
        # Given: Network is down
        # When: Service starts
        # Then: Service enters retrying_rapid state
        # And: Health status is "waiting"
        
    async def test_network_recovery(self):
        """Service recovers when network becomes available"""
        # Given: Service is in retrying_persistent state
        # When: Network becomes available
        # Then: Connection succeeds within 5 minutes
        # And: Health status becomes "healthy"
        
    async def test_infinite_retry(self):
        """Service never stops retrying"""
        # Given: Network remains down
        # When: Service has been retrying for 2 hours
        # Then: Service is still retrying
        # And: Health status is still "waiting"
        # And: Service has not stopped (is_running == True)
        
    async def test_circuit_breaker_activation(self):
        """Circuit breaker activates after threshold failures"""
        # Given: 50 consecutive connection failures
        # When: Next connection attempt fails
        # Then: Circuit breaker opens
        # And: Service pauses for 5 minutes
        # And: Health status is "circuit_open"
        
    async def test_circuit_breaker_recovery(self):
        """Circuit breaker closes after successful connection"""
        # Given: Circuit breaker is open
        # When: Timeout expires and connection succeeds
        # Then: Circuit breaker closes
        # And: Health status returns to "healthy"
        
    async def test_retry_stage_progression(self):
        """Service progresses through retry stages"""
        # Given: Service is disconnected
        # When: Retries fail
        # Then: Service progresses: rapid -> moderate -> persistent
        # And: Delays increase appropriately
        
    async def test_transient_failure_recovery(self):
        """Service quickly recovers from brief failures"""
        # Given: Service is healthy and active
        # When: Brief network interruption (10 seconds)
        # Then: Service reconnects within 30 seconds
        # And: Event ingestion resumes
```

#### 4.2 Chaos Engineering Tests

```python
class TestChaosScenarios:
    """Chaos engineering tests"""
    
    async def test_intermittent_network(self):
        """Handle intermittent network (up/down cycles)"""
        
    async def test_dns_failures(self):
        """Handle DNS resolution failures"""
        
    async def test_ssl_cert_issues(self):
        """Handle SSL certificate problems"""
        
    async def test_partial_connectivity(self):
        """Handle partial connectivity (HTTP OK, WebSocket fails)"""
        
    async def test_slow_network(self):
        """Handle very slow network responses"""
        
    async def test_connection_timeouts(self):
        """Handle connection timeout scenarios"""
```

---

## Implementation Roadmap

### Sprint 1: Core Retry Logic (Week 1)
- [ ] **Task 1.1:** Implement `RetryStrategy` class with staged retry
- [ ] **Task 1.2:** Implement `ConnectionState` state machine
- [ ] **Task 1.3:** Update `connection_manager.py` to use infinite retry
- [ ] **Task 1.4:** Add `CircuitBreaker` class
- [ ] **Task 1.5:** Integration testing for retry logic
- [ ] **Task 1.6:** Update `_reconnect_loop()` to never set `is_running = False`

**Deliverables:**
- Modified `connection_manager.py` with infinite retry
- New `retry_strategy.py` module
- New `circuit_breaker.py` module
- Unit tests for retry logic

### Sprint 2: Health Checks & Monitoring (Week 2)
- [ ] **Task 2.1:** Implement `HealthStatus` enum and `HealthDetail` class
- [ ] **Task 2.2:** Update health check endpoint with detailed status
- [ ] **Task 2.3:** Implement `ConnectionMetrics` class
- [ ] **Task 2.4:** Add Prometheus metrics endpoint
- [ ] **Task 2.5:** Update dashboard to show retry state
- [ ] **Task 2.6:** Add alerting rules

**Deliverables:**
- Enhanced health check API
- Prometheus metrics integration
- Dashboard UI updates
- Alert configuration

### Sprint 3: Configuration & Testing (Week 3)
- [ ] **Task 3.1:** Add environment variables for retry configuration
- [ ] **Task 3.2:** Implement preset retry strategies
- [ ] **Task 3.3:** Add configuration validation
- [ ] **Task 3.4:** Write resilience tests
- [ ] **Task 3.5:** Write chaos engineering tests
- [ ] **Task 3.6:** Performance testing under retry load

**Deliverables:**
- Configuration documentation
- Test suite (80%+ coverage)
- Performance benchmarks

### Sprint 4: Documentation & Rollout (Week 4)
- [ ] **Task 4.1:** Update README with resilience features
- [ ] **Task 4.2:** Create operator's guide for retry configuration
- [ ] **Task 4.3:** Create troubleshooting guide
- [ ] **Task 4.4:** Update deployment scripts
- [ ] **Task 4.5:** Staged rollout to production
- [ ] **Task 4.6:** Post-deployment monitoring

**Deliverables:**
- Complete documentation
- Deployment guide
- Runbook for operations

---

## Files to Modify

### Core Changes
1. **`services/websocket-ingestion/src/connection_manager.py`**
   - Remove `max_retries` limit
   - Implement staged retry strategy
   - Add circuit breaker
   - Never set `is_running = False` in retry loop

2. **`services/websocket-ingestion/src/websocket_client.py`**
   - Update retry logic
   - Add connection state tracking

3. **`services/websocket-ingestion/src/health_check.py`**
   - Implement detailed health status
   - Add retry state information
   - Provide recovery recommendations

### New Files
4. **`services/websocket-ingestion/src/retry_strategy.py`** (NEW)
   - `RetryStrategy` class
   - Staged retry configuration
   - Backoff calculation

5. **`services/websocket-ingestion/src/circuit_breaker.py`** (NEW)
   - `CircuitBreaker` class
   - Failure tracking
   - Timeout management

6. **`services/websocket-ingestion/src/connection_metrics.py`** (NEW)
   - `ConnectionMetrics` class
   - Prometheus metrics
   - Performance tracking

7. **`tests/resilience/test_network_resilience.py`** (NEW)
   - Resilience test suite
   - Chaos engineering tests

### Configuration
8. **`docker-compose.yml`**
   - Add retry configuration environment variables
   - Set defaults for infinite retry

9. **`infrastructure/env.example`**
   - Document retry configuration options
   - Add preset strategy examples

### Documentation
10. **`docs/RESILIENCE_GUIDE.md`** (NEW)
    - Resilience features overview
    - Configuration guide
    - Troubleshooting

11. **`README.md`**
    - Update features section
    - Add resilience highlights

---

## Risk Assessment

### Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Increased resource usage from infinite retry | MEDIUM | Circuit breaker limits retry rate; configurable delays |
| Memory leaks from long-running retry loops | MEDIUM | Proper cleanup in async tasks; memory monitoring |
| Log spam from continuous failures | LOW | Log level adjustment after N failures; log aggregation |
| Difficulty debugging connection issues | LOW | Detailed health status; comprehensive metrics |
| Breaking changes for existing deployments | LOW | Backward compatible; default to infinite retry |

### Rollback Plan

If issues arise:
1. Set environment variable: `WEBSOCKET_RETRY_STRATEGY=limited`
2. This reverts to legacy behavior (10 retry limit)
3. Restart affected services
4. Investigate issues in staging environment

---

## Success Criteria

### Functional Requirements
- ✅ Service never permanently stops due to network issues
- ✅ Service recovers automatically when network returns
- ✅ Health checks accurately reflect retry state
- ✅ Circuit breaker prevents resource exhaustion
- ✅ All tests pass (including chaos tests)

### Performance Requirements
- ✅ Connection recovery within 5 minutes of network return
- ✅ Resource usage remains stable during extended outages
- ✅ No memory leaks during 24+ hour retry periods
- ✅ Dashboard remains responsive during retry states

### Operational Requirements
- ✅ Clear visibility into connection state via dashboard
- ✅ Operators can tune retry behavior via environment variables
- ✅ Alerts fire appropriately for different failure scenarios
- ✅ Documentation complete and accurate

---

## Future Enhancements (Post-V1)

### Phase 5: Advanced Features
1. **Adaptive Retry:**
   - Learn from failure patterns
   - Adjust retry strategy based on historical data
   - Detect time-of-day patterns (e.g., scheduled maintenance)

2. **Multiple Connection Endpoints:**
   - Fallback to Nabu Casa if local fails
   - Round-robin between multiple HA instances
   - Health-based endpoint selection

3. **Predictive Alerts:**
   - Predict when connection might fail
   - Alert before complete outage
   - Proactive remediation

4. **Self-Healing:**
   - Auto-restart container if stuck
   - Auto-rotate credentials on auth failures
   - Auto-update DNS cache

---

## Conclusion

This enhancement transforms the HA Ingestor from a **fail-and-stop** service to a **resilient, self-healing** service that gracefully handles network disruptions. The infinite retry strategy with circuit breaker protection ensures the service will automatically recover from any transient failure while protecting system resources during extended outages.

**Next Steps:**
1. Review and approve this plan
2. Prioritize sprints based on urgency
3. Begin Sprint 1 implementation
4. Set up staging environment for testing

---

**Questions for Review:**
1. Do the retry stages (rapid/moderate/persistent) align with your operational needs?
2. Are the default timeouts appropriate (5s, 30s, 5min)?
3. Should we implement all 4 sprints or focus on Sprint 1-2 first?
4. Do you want to include the chaos engineering tests in initial release?
5. Any specific failure scenarios we should prioritize testing?


# Network Resilience - Simple Fix

**Problem:** WebSocket service gives up after 10 retry attempts and stops permanently.

**Solution:** Make it retry indefinitely (or for a very long time).

---

## Simple Implementation (15 minutes)

### Option 1: Infinite Retry (Recommended)

**Change 1 line in `services/websocket-ingestion/src/connection_manager.py`:**

```python
# Line 40 - BEFORE:
self.max_retries = 10  # ❌ Stops after 10 attempts

# Line 40 - AFTER:
self.max_retries = -1  # ✅ Retry forever (-1 = infinite)
```

**Update the check in `_reconnect_loop()` (Line 167):**

```python
# BEFORE:
while self.is_running and self.current_retry_count < self.max_retries:

# AFTER:
while self.is_running and (self.max_retries == -1 or self.current_retry_count < self.max_retries):
```

**That's it!** Service will now retry forever.

---

### Option 2: Very High Limit

If you prefer a safety limit (prevents truly pathological cases):

```python
# Line 40:
self.max_retries = 1000  # ~16 hours at max backoff
```

This gives you 1000 attempts. With current backoff, that's many hours of retrying.

---

### Option 3: Configurable (Slightly More Work)

Make it configurable via environment variable:

**1. Update `services/websocket-ingestion/src/connection_manager.py`:**

```python
# Line 24 (in __init__):
self.max_retries = int(os.getenv('WEBSOCKET_MAX_RETRIES', '-1'))  # Default: infinite
```

**2. Add to `docker-compose.yml`:**

```yaml
websocket-ingestion:
  environment:
    - WEBSOCKET_MAX_RETRIES=${WEBSOCKET_MAX_RETRIES:--1}  # -1 = infinite
```

**3. Document in `infrastructure/env.example`:**

```bash
# WebSocket Retry Configuration
WEBSOCKET_MAX_RETRIES=-1  # -1 for infinite retry, or set a number (e.g., 100)
```

Now operators can control it without code changes.

---

## Additional Nice-to-Have (Optional, 30 minutes)

### Cap the Maximum Delay

Current backoff can grow very large. Cap it at 5 minutes:

```python
# Line 42-43 - ADD:
self.max_delay = int(os.getenv('WEBSOCKET_MAX_RETRY_DELAY', '300'))  # 5 minutes default
```

Update `_calculate_delay()` to use it (it already does on line 233).

---

## Testing

**Test 1: Startup Without Network**
```bash
# 1. Ensure HA is unreachable
# 2. Start service
docker-compose up websocket-ingestion

# 3. Watch logs - should keep retrying
docker logs -f ha-ingestor-websocket

# 4. Make HA available
# 5. Service should connect within max_delay (60s currently)
```

**Test 2: Extended Outage**
```bash
# 1. Service running and connected
# 2. Disconnect HA
# 3. Wait 1 hour
# 4. Reconnect HA
# 5. Service should recover
```

---

## What We're NOT Doing (Avoiding Over-Engineering)

- ❌ Complex state machine
- ❌ Circuit breaker pattern (not needed for this problem)
- ❌ Multiple retry stages
- ❌ New files and abstractions
- ❌ Comprehensive metrics system
- ❌ Chaos engineering framework

**Why?** The current retry logic already works well. It just needs to run longer.

---

## Recommendation

**Quick Win (Today):**
- Implement Option 3 (Configurable)
- Set default to `-1` (infinite)
- Cap max_delay at 300 seconds (5 min)
- Test with network down scenario
- Deploy

**Total Changes:**
- 3 lines of code
- 1 environment variable
- 5 minutes to implement
- 10 minutes to test

**Future Enhancements (If Needed Later):**
- Enhanced health status ("retrying" vs "failed")
- Better dashboard visibility into retry state
- Metrics on retry attempts
- Only add these if they become actual problems

---

## Implementation Now

Want me to make these changes right now? I'll:
1. Update `connection_manager.py` (3 lines)
2. Update `docker-compose.yml` (1 line)
3. Update `env.example` (document it)
4. Test it works

Should take about 10 minutes total.


# WattTime Integration Improvement Plan

**Date:** 2025-01-15  
**Service:** Carbon Intensity Service (Port 8010)  
**Current Status:** ⚠️ Token-based, no auto-refresh  
**Goal:** Reliable, consistent operation with automatic token management

---

## Executive Summary

The Carbon Intensity Service is **well-architected** but has a critical flaw: it requires a static `WATTTIME_API_TOKEN` that expires every 30 minutes. This plan implements automatic token refresh and improved error handling to ensure consistent operation.

---

## Current State Analysis

### ✅ What's Working Well

1. **Clean Architecture**
   - Separation of concerns (fetch, store, health check)
   - Proper async/await patterns
   - InfluxDB integration working
   - Health check endpoint functional
   - Docker containerization complete

2. **Good Practices**
   - Error handling with fallback to cache
   - Logging with context
   - 15-minute fetch interval (appropriate)
   - Non-root user in Docker
   - Health checks configured

3. **Data Flow**
   ```
   WattTime API → Service → InfluxDB (carbon_intensity measurement)
                         → Health Dashboard (Data Sources tab)
   ```

### ❌ Critical Issues

1. **Token Expiration Problem**
   ```python
   # Line 37: Uses static token
   self.api_token = os.getenv('WATTTIME_API_TOKEN')
   
   # Line 106: Bearer token auth
   headers = {"Authorization": f"Bearer {self.api_token}"}
   ```
   
   **Problem:** Tokens expire after 30 minutes, service requires manual restart

2. **No Credential Storage**
   - No username/password environment variables
   - Can't automatically refresh token
   - Requires manual token management

3. **Limited Error Context**
   - Doesn't distinguish between expired token vs other errors
   - No specific handling for HTTP 401 (expired token)
   - Generic error handling for all auth failures

### ⚠️ Minor Issues

1. **InfluxDB Client Version**
   - Using `influxdb3-python` (v3 client)
   - May have TLS/SSL issues (seen in other services)
   - Consider using `influxdb-client` (v2 API, more stable)

2. **No Retry Logic**
   - Single attempt per fetch
   - Should retry on transient failures
   - Should have exponential backoff

3. **Limited Region Validation**
   - Accepts any region string
   - No validation against WattTime supported regions
   - No automatic region lookup

---

## Improvement Plan

### **Phase 1: Add Automatic Token Refresh** (Priority: HIGH)

#### Changes Required

**1.1 Update Environment Variables**

Add to `infrastructure/env.example`:
```bash
# WattTime Authentication (Choose ONE method)

# Method 1: Static Token (Current - requires manual refresh every 30 min)
#WATTTIME_API_TOKEN=your_token_here

# Method 2: Username/Password (Recommended - automatic token refresh)
WATTTIME_USERNAME=your_username
WATTTIME_PASSWORD=your_password

# Grid Configuration
GRID_REGION=CAISO_NORTH
```

**1.2 Update Service Constructor**

```python
class CarbonIntensityService:
    def __init__(self):
        # Authentication credentials
        self.username = os.getenv('WATTTIME_USERNAME')
        self.password = os.getenv('WATTTIME_PASSWORD')
        self.api_token = os.getenv('WATTTIME_API_TOKEN')  # Optional fallback
        
        # Token management
        self.token_expires_at: Optional[datetime] = None
        self.token_refresh_buffer = 300  # Refresh 5 min before expiry
        
        # Configuration
        self.region = os.getenv('GRID_REGION', 'CAISO_NORTH')
        self.base_url = "https://api.watttime.org/v3"
        
        # Validate authentication
        if not self.username or not self.password:
            if not self.api_token:
                raise ValueError(
                    "Either WATTTIME_USERNAME/PASSWORD or WATTTIME_API_TOKEN required"
                )
            logger.warning("Using static token - will expire in 30 minutes")
```

**1.3 Add Token Refresh Method**

```python
async def refresh_token(self) -> bool:
    """
    Refresh WattTime API token using username/password
    
    Returns:
        bool: True if refresh successful, False otherwise
    """
    if not self.username or not self.password:
        logger.error("Cannot refresh token: username/password not configured")
        return False
    
    try:
        url = f"{self.base_url}/login"
        auth = aiohttp.BasicAuth(self.username, self.password)
        
        log_with_context(
            logger, "INFO",
            "Refreshing WattTime API token",
            service="carbon-intensity-service"
        )
        
        async with self.session.post(url, auth=auth) as response:
            if response.status == 200:
                data = await response.json()
                self.api_token = data.get('token')
                
                # WattTime tokens expire in 30 minutes
                self.token_expires_at = datetime.now() + timedelta(minutes=30)
                
                logger.info(f"Token refreshed successfully, expires at {self.token_expires_at}")
                return True
            else:
                log_error_with_context(
                    logger,
                    f"Token refresh failed with status {response.status}",
                    service="carbon-intensity-service",
                    status_code=response.status
                )
                return False
                
    except Exception as e:
        log_error_with_context(
            logger,
            f"Error refreshing token: {e}",
            service="carbon-intensity-service",
            error=str(e)
        )
        return False


async def ensure_valid_token(self) -> bool:
    """
    Ensure we have a valid token, refresh if needed
    
    Returns:
        bool: True if we have a valid token, False otherwise
    """
    # If no expiration time set and we have username/password, refresh now
    if not self.token_expires_at and self.username and self.password:
        return await self.refresh_token()
    
    # If token expires soon (within buffer time), refresh now
    if self.token_expires_at:
        time_until_expiry = (self.token_expires_at - datetime.now()).total_seconds()
        if time_until_expiry < self.token_refresh_buffer:
            logger.info(f"Token expires in {time_until_expiry}s, refreshing...")
            return await self.refresh_token()
    
    return True  # Token still valid
```

**1.4 Update Fetch Method**

```python
async def fetch_carbon_intensity(self) -> Optional[Dict[str, Any]]:
    """Fetch carbon intensity from WattTime API"""
    
    try:
        # Ensure we have a valid token
        if not await self.ensure_valid_token():
            logger.error("No valid token available")
            self.health_handler.failed_fetches += 1
            return self.cached_data
        
        url = f"{self.base_url}/forecast"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        params = {"region": self.region}
        
        log_with_context(
            logger, "INFO",
            f"Fetching carbon intensity for region {self.region}",
            service="carbon-intensity-service",
            region=self.region
        )
        
        async with self.session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                # ... existing success handling ...
                
            elif response.status == 401:
                # Token expired mid-request, try refresh
                log_error_with_context(
                    logger,
                    "Authentication failed (401), attempting token refresh",
                    service="carbon-intensity-service"
                )
                
                if await self.refresh_token():
                    logger.info("Token refreshed, retrying request...")
                    # Retry once with new token
                    headers = {"Authorization": f"Bearer {self.api_token}"}
                    async with self.session.get(url, headers=headers, params=params) as retry_response:
                        if retry_response.status == 200:
                            raw_data = await retry_response.json()
                            # ... parse and return ...
                
                self.health_handler.failed_fetches += 1
                return self.cached_data
                
            else:
                # ... existing error handling ...
```

**1.5 Update Startup Method**

```python
async def startup(self):
    """Initialize service components"""
    logger.info("Initializing Carbon Intensity Service...")
    
    # Create HTTP session
    self.session = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=10)
    )
    
    # If using username/password, get initial token
    if self.username and self.password:
        logger.info("Obtaining initial API token...")
        if not await self.refresh_token():
            raise ValueError("Failed to obtain initial API token")
    
    # Create InfluxDB client
    self.influxdb_client = InfluxDBClient3(
        host=self.influxdb_url,
        token=self.influxdb_token,
        database=self.influxdb_bucket,
        org=self.influxdb_org
    )
    
    logger.info("Carbon Intensity Service initialized successfully")
```

---

### **Phase 2: Improve Error Handling** (Priority: MEDIUM)

#### Changes Required

**2.1 Add Retry Logic with Exponential Backoff**

```python
async def fetch_with_retry(
    self,
    max_retries: int = 3,
    base_delay: int = 2
) -> Optional[Dict[str, Any]]:
    """
    Fetch carbon intensity with retry logic
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (doubles each retry)
        
    Returns:
        Carbon intensity data or None
    """
    for attempt in range(max_retries):
        try:
            result = await self.fetch_carbon_intensity()
            if result:
                return result
                
        except aiohttp.ClientError as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Fetch failed (attempt {attempt+1}/{max_retries}), retrying in {delay}s...")
                await asyncio.sleep(delay)
            else:
                log_error_with_context(
                    logger,
                    f"All {max_retries} attempts failed",
                    service="carbon-intensity-service",
                    error=str(e)
                )
    
    return None
```

**2.2 Add Specific Error Handling**

```python
async def handle_api_error(self, response: aiohttp.ClientResponse) -> str:
    """
    Handle specific API error responses
    
    Args:
        response: aiohttp response object
        
    Returns:
        Error message string
    """
    if response.status == 401:
        return "Authentication failed - token expired or invalid"
    elif response.status == 403:
        return f"Access denied - region '{self.region}' not available on your plan"
    elif response.status == 404:
        return f"Region '{self.region}' not found"
    elif response.status == 429:
        return "Rate limit exceeded - too many requests"
    elif response.status >= 500:
        return f"WattTime server error ({response.status})"
    else:
        return f"Unexpected error ({response.status})"
```

**2.3 Enhanced Health Check**

Update `health_check.py`:

```python
class HealthCheckHandler:
    def __init__(self):
        self.start_time = datetime.now()
        self.last_successful_fetch = None
        self.last_token_refresh = None
        self.total_fetches = 0
        self.failed_fetches = 0
        self.token_refresh_count = 0
        self.consecutive_failures = 0
    
    async def handle(self, request):
        """Handle health check request with enhanced metrics"""
        
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        # Determine health status
        healthy = True
        status_reasons = []
        
        # Check last successful fetch
        if self.last_successful_fetch:
            time_since_last = (datetime.now() - self.last_successful_fetch).total_seconds()
            if time_since_last > 1800:  # 30 minutes
                healthy = False
                status_reasons.append(f"No successful fetch in {time_since_last//60:.0f} minutes")
        else:
            healthy = False
            status_reasons.append("No successful fetches yet")
        
        # Check consecutive failures
        if self.consecutive_failures > 3:
            healthy = False
            status_reasons.append(f"{self.consecutive_failures} consecutive failures")
        
        # Success rate check
        success_rate = (
            (self.total_fetches - self.failed_fetches) / self.total_fetches 
            if self.total_fetches > 0 else 0
        )
        if success_rate < 0.8 and self.total_fetches > 10:
            healthy = False
            status_reasons.append(f"Success rate only {success_rate*100:.1f}%")
        
        status = {
            "status": "healthy" if healthy else "degraded",
            "service": "carbon-intensity-service",
            "uptime_seconds": uptime,
            "last_successful_fetch": (
                self.last_successful_fetch.isoformat() 
                if self.last_successful_fetch else None
            ),
            "last_token_refresh": (
                self.last_token_refresh.isoformat() 
                if self.last_token_refresh else None
            ),
            "total_fetches": self.total_fetches,
            "failed_fetches": self.failed_fetches,
            "consecutive_failures": self.consecutive_failures,
            "token_refresh_count": self.token_refresh_count,
            "success_rate": success_rate,
            "timestamp": datetime.now().isoformat(),
            "issues": status_reasons if not healthy else []
        }
        
        return web.json_response(status, status=200 if healthy else 503)
```

---

### **Phase 3: Add Region Validation** (Priority: LOW)

**3.1 Region Lookup Endpoint**

```python
async def lookup_region(self, latitude: float, longitude: float) -> Optional[str]:
    """
    Look up grid region for given coordinates
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        
    Returns:
        Region identifier or None
    """
    try:
        if not await self.ensure_valid_token():
            return None
        
        url = f"{self.base_url}/region-from-loc"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        params = {"latitude": latitude, "longitude": longitude}
        
        async with self.session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                region = data.get('region')
                logger.info(f"Region lookup: ({latitude}, {longitude}) → {region}")
                return region
            else:
                logger.error(f"Region lookup failed: {response.status}")
                return None
                
    except Exception as e:
        logger.error(f"Error looking up region: {e}")
        return None


async def validate_region(self) -> bool:
    """
    Validate that configured region is accessible
    
    Returns:
        bool: True if region is valid and accessible
    """
    try:
        if not await self.ensure_valid_token():
            return False
        
        url = f"{self.base_url}/forecast"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        params = {"region": self.region}
        
        async with self.session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                logger.info(f"Region '{self.region}' validated successfully")
                return True
            elif response.status == 403:
                logger.error(f"Region '{self.region}' not accessible on your WattTime plan")
                return False
            elif response.status == 404:
                logger.error(f"Region '{self.region}' not found")
                return False
            else:
                logger.warning(f"Region validation returned {response.status}")
                return False
                
    except Exception as e:
        logger.error(f"Error validating region: {e}")
        return False
```

**3.2 Startup Validation**

```python
async def startup(self):
    """Initialize service components"""
    logger.info("Initializing Carbon Intensity Service...")
    
    # ... existing session creation ...
    
    # Get initial token
    if self.username and self.password:
        if not await self.refresh_token():
            raise ValueError("Failed to obtain initial API token")
    
    # Validate region
    logger.info(f"Validating region '{self.region}'...")
    if not await self.validate_region():
        raise ValueError(
            f"Region '{self.region}' is not valid or accessible. "
            "Check your WattTime plan or use region lookup."
        )
    
    # ... existing InfluxDB setup ...
```

---

### **Phase 4: Configuration Updates** (Priority: HIGH)

**4.1 Update `docker-compose.yml`**

```yaml
carbon-intensity:
  build:
    context: .
    dockerfile: services/carbon-intensity-service/Dockerfile
  container_name: homeiq-carbon-intensity
  restart: unless-stopped
  ports:
    - "8010:8010"
  environment:
    # WattTime Authentication (username/password preferred)
    - WATTTIME_USERNAME=${WATTTIME_USERNAME:-}
    - WATTTIME_PASSWORD=${WATTTIME_PASSWORD:-}
    # Or static token (for testing/fallback)
    - WATTTIME_API_TOKEN=${WATTTIME_API_TOKEN:-}
    # Grid configuration
    - GRID_REGION=${GRID_REGION:-CAISO_NORTH}
    # InfluxDB configuration
    - INFLUXDB_URL=http://influxdb:8086
    - INFLUXDB_TOKEN=${INFLUXDB_TOKEN:-homeiq-token}
    - INFLUXDB_ORG=${INFLUXDB_ORG:-homeiq}
    - INFLUXDB_BUCKET=${INFLUXDB_BUCKET:-home_assistant_events}
    - SERVICE_PORT=8010
    - LOG_LEVEL=${LOG_LEVEL:-INFO}
  depends_on:
    influxdb:
      condition: service_healthy
  networks:
    - homeiq-network
  deploy:
    resources:
      limits:
        memory: 128M
      reservations:
        memory: 64M
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
      labels: "service=carbon-intensity,environment=production"
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8010/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 30s
```

**4.2 Update `infrastructure/env.example`**

```bash
# =============================================================================
# Carbon Intensity Configuration (WattTime API)
# =============================================================================

# Authentication Method (Choose ONE):

# Method 1: Username/Password (RECOMMENDED - automatic token refresh)
WATTTIME_USERNAME=your_watttime_username
WATTTIME_PASSWORD=your_watttime_password

# Method 2: Static API Token (NOT RECOMMENDED - expires every 30 minutes)
# WATTTIME_API_TOKEN=your_token_here

# Grid Region Configuration
# US Regions: CAISO_NORTH, CAISO_SOUTH, ERCOT, PJM, NYISO, ISONE, MISO
# International: Contact WattTime for available regions
GRID_REGION=CAISO_NORTH

# Notes:
# - Free tier: Limited to 1-2 regions (typically US only)
# - Paid tier: Global coverage (12+ countries)
# - Use region lookup API to find your region
```

---

## Implementation Checklist

### Phase 1: Token Refresh (HIGH PRIORITY)
- [ ] Update `CarbonIntensityService.__init__()` to accept username/password
- [ ] Add `refresh_token()` method
- [ ] Add `ensure_valid_token()` method
- [ ] Update `fetch_carbon_intensity()` to call `ensure_valid_token()`
- [ ] Update `startup()` to get initial token
- [ ] Add 401 error handling with retry
- [ ] Update docker-compose.yml environment variables
- [ ] Update infrastructure/env.example
- [ ] Test token refresh logic
- [ ] Deploy and verify

### Phase 2: Error Handling (MEDIUM PRIORITY)
- [ ] Add `fetch_with_retry()` method with exponential backoff
- [ ] Add `handle_api_error()` method for specific errors
- [ ] Update health check with enhanced metrics
- [ ] Add consecutive failure tracking
- [ ] Add token refresh count tracking
- [ ] Test error scenarios
- [ ] Deploy and verify

### Phase 3: Region Validation (LOW PRIORITY)
- [ ] Add `lookup_region()` method
- [ ] Add `validate_region()` method
- [ ] Add region validation to startup
- [ ] Create region lookup CLI tool
- [ ] Document supported regions
- [ ] Test with different regions
- [ ] Deploy and verify

### Phase 4: Testing & Documentation
- [ ] Write unit tests for token refresh
- [ ] Write integration tests for API calls
- [ ] Test token expiration scenarios
- [ ] Test error handling and retries
- [ ] Update service README
- [ ] Create setup guide
- [ ] Document troubleshooting steps

---

## Testing Plan

### Unit Tests

```python
# tests/test_carbon_intensity.py

import pytest
from unittest.mock import AsyncMock, patch
from services.carbon_intensity.src.main import CarbonIntensityService

@pytest.mark.asyncio
async def test_token_refresh_success():
    """Test successful token refresh"""
    service = CarbonIntensityService()
    service.username = "test_user"
    service.password = "test_pass"
    service.session = AsyncMock()
    
    # Mock successful response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"token": "new_token"})
    service.session.post.return_value.__aenter__.return_value = mock_response
    
    result = await service.refresh_token()
    
    assert result == True
    assert service.api_token == "new_token"
    assert service.token_expires_at is not None

@pytest.mark.asyncio
async def test_token_refresh_failure():
    """Test failed token refresh"""
    service = CarbonIntensityService()
    service.username = "test_user"
    service.password = "wrong_pass"
    service.session = AsyncMock()
    
    # Mock failed response
    mock_response = AsyncMock()
    mock_response.status = 401
    service.session.post.return_value.__aenter__.return_value = mock_response
    
    result = await service.refresh_token()
    
    assert result == False

@pytest.mark.asyncio
async def test_ensure_valid_token_refresh_needed():
    """Test token refresh when token expires soon"""
    service = CarbonIntensityService()
    service.username = "test_user"
    service.password = "test_pass"
    service.token_expires_at = datetime.now() + timedelta(minutes=2)  # Expires soon
    service.refresh_token = AsyncMock(return_value=True)
    
    result = await service.ensure_valid_token()
    
    assert result == True
    service.refresh_token.assert_called_once()
```

### Integration Tests

```bash
# Test token refresh
docker-compose exec carbon-intensity python -c "
from src.main import CarbonIntensityService
import asyncio

async def test():
    service = CarbonIntensityService()
    await service.startup()
    result = await service.refresh_token()
    print(f'Token refresh: {result}')
    print(f'Token: {service.api_token[:20]}...')

asyncio.run(test())
"

# Test API call
curl http://localhost:8010/health

# Check InfluxDB data
curl -X POST "http://localhost:8086/api/v2/query?org=homeiq" \
  -H "Authorization: Token homeiq-token" \
  -H "Content-Type: application/vnd.flux" \
  -d 'from(bucket:"home_assistant_events")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "carbon_intensity")
  |> last()'
```

---

## Deployment Steps

### Step 1: Backup Current Configuration
```bash
cp infrastructure/env.example infrastructure/env.example.backup
cp docker-compose.yml docker-compose.yml.backup
```

### Step 2: Update Code
- Implement Phase 1 changes
- Run linter and tests
- Build Docker image

### Step 3: Update Configuration
```bash
# Add to .env or docker-compose.yml
WATTTIME_USERNAME=your_username
WATTTIME_PASSWORD=your_password
GRID_REGION=CAISO_NORTH
```

### Step 4: Deploy
```bash
# Rebuild service
docker-compose build carbon-intensity

# Deploy with new configuration
docker-compose up -d carbon-intensity

# Watch logs
docker logs -f homeiq-carbon-intensity
```

### Step 5: Verify
```bash
# Check health
curl http://localhost:8010/health | jq

# Should show:
# - status: "healthy"
# - last_token_refresh: recent timestamp
# - token_refresh_count: > 0

# Check InfluxDB data
# (query command from integration tests)
```

---

## Success Metrics

### Before Implementation
- ⚠️ Token expires every 30 minutes
- ⚠️ Manual service restart required
- ⚠️ ~96 daily restarts needed (24 hours * 2)
- ⚠️ Data gaps during token expiration

### After Implementation
- ✅ Automatic token refresh every 25 minutes
- ✅ No manual intervention required
- ✅ Continuous operation
- ✅ No data gaps
- ✅ Health check shows token refresh activity

---

## Rollback Plan

If deployment fails:

```bash
# Stop new version
docker-compose stop carbon-intensity

# Restore backups
cp infrastructure/env.example.backup infrastructure/env.example
cp docker-compose.yml.backup docker-compose.yml

# Deploy old version
docker-compose up -d carbon-intensity
```

---

## Timeline

**Phase 1 (Token Refresh):** 4-6 hours
- Code changes: 2 hours
- Testing: 1 hour
- Deployment: 1 hour
- Verification: 1-2 hours (wait for token refresh cycles)

**Phase 2 (Error Handling):** 2-3 hours
- Code changes: 1 hour
- Testing: 30 minutes
- Deployment: 30 minutes
- Verification: 30 minutes

**Phase 3 (Region Validation):** 1-2 hours
- Code changes: 30 minutes
- Testing: 30 minutes
- Deployment: 15 minutes
- Verification: 15 minutes

**Total:** 7-11 hours

---

## Next Steps

1. **Register with WattTime** (if not done)
   - Get username and password
   - Determine your grid region

2. **Implement Phase 1** (token refresh)
   - Highest priority
   - Enables consistent operation

3. **Test Thoroughly**
   - Verify token refresh works
   - Wait for multiple refresh cycles

4. **Monitor in Production**
   - Check health endpoint regularly
   - Monitor InfluxDB data flow
   - Watch for errors in logs

5. **Implement Phases 2 & 3** (as needed)
   - Error handling improvements
   - Region validation

---

**Status:** Ready to implement! Token refresh will solve the critical consistency issue. 🚀


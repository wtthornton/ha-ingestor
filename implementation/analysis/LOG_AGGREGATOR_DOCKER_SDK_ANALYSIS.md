# Log Aggregator Docker SDK Issue Analysis

**Date:** October 19, 2025  
**Issue:** Docker SDK failing to connect with "Not supported URL scheme http+docker" error  
**Service:** log-aggregator (homeiq-log-aggregator)

---

## Problem Summary

The log-aggregator service cannot initialize a Docker client connection, resulting in:
```
ERROR: Failed to initialize Docker client: Error while fetching server API version: Not supported URL scheme http+docker
```

This prevents the service from collecting logs from other Docker containers.

---

## Root Cause Analysis

### 1. **urllib3 v2.0+ Breaking Changes**
The error "http+docker" indicates that the `requests` library (used by docker-py) is encountering an unsupported URL scheme when trying to connect to the Unix socket at `/var/run/docker.sock`.

**Key Issue:** docker-py versions < 7.0.0 may have compatibility issues with urllib3 v2.0+, which was released in 2023 and introduced breaking changes to socket handling.

### 2. **Current Configuration Issues**

**Problematic setup:**
```python
# services/log-aggregator/requirements.txt
docker==6.1.3  # Released 2023, may not support urllib3 v2.0+
requests-unixsocket==0.3.0  # May be redundant or conflicting
```

**Docker SDK versions:**
- `docker==6.1.3` - Released June 2023 (OUTDATED)
- `docker==7.0.0` - Released November 2023 (first to fully support urllib3 v2.0)
- `docker==7.1.0` - Released February 2024 (stable)
- `docker==7.2.0+` - Latest versions as of October 2025

### 3. **Unix Socket Connection Requirements**

Based on Context7 documentation:
- `docker.from_env()` should auto-detect socket connection
- No need for `requests-unixsocket` in modern versions
- Requires proper group permissions for socket access

---

## Version Compatibility Matrix (2025)

| Component | Current Version | Recommended Version | Notes |
|-----------|----------------|--------------------|---------| 
| **docker** | 6.1.3 | 7.1.0 | Latest stable, full urllib3 v2.x support |
| **urllib3** | (transitive) | 2.2.x | Auto-installed by docker SDK |
| **requests** | (transitive) | 2.31.x+ | Auto-installed by docker SDK |
| **requests-unixsocket** | 0.3.0 | **REMOVE** | Not needed in docker 7.x+ |

### Why docker 7.1.0?

1. **Full urllib3 v2.x compatibility** - No "http+docker" errors
2. **Better Windows Docker Desktop support** - Works with WSL2 backend
3. **Improved socket handling** - Automatic detection and fallback
4. **Security updates** - Latest CVE patches
5. **Python 3.11+ optimization** - Better performance

---

## Correct Implementation Pattern (Context7)

### Recommended Approach for 2025:

```python
import docker

# Method 1: Auto-detection (RECOMMENDED)
try:
    client = docker.from_env()
    client.ping()
    logger.info("✅ Docker client initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize Docker client: {e}")
    client = None

# Method 2: Explicit socket (fallback if needed)
try:
    client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
    client.ping()
except Exception as e:
    logger.error(f"❌ Explicit socket connection failed: {e}")
```

**Key Points:**
- No need to import `docker.api` or use `APIClient` for basic operations
- `from_env()` handles socket detection automatically
- Ping test verifies connection before use
- Windows Docker Desktop compatibility built-in

---

## Docker Compose Configuration

### Current Setup (CORRECT):
```yaml
log-aggregator:
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro  # ✅ Read-only socket mount
  group_add:
    - "0"  # ✅ root group for socket access
```

**Why this works:**
- Socket mounted as read-only (security best practice)
- User added to root group (GID 0) for socket access
- No need to run as root user

---

## Dockerfile Configuration

### Current Setup (MOSTLY CORRECT):
```dockerfile
# Create non-root user with docker group access
RUN groupadd -g 999 docker || true && \
    groupadd -g 1001 appgroup && \
    useradd -r -u 1001 -g appgroup -G docker appuser

USER appuser
```

**Issue:** GID 999 may not match actual docker group on host

**Fix:** Use `group_add` in docker-compose instead (already done ✅)

---

## Recommended Fix Plan

### Phase 1: Update Dependencies (CRITICAL)
```txt
# services/log-aggregator/requirements.txt
aiohttp==3.9.1
aiofiles==23.2.1
docker==7.1.0  # ⬆️ UPGRADE from 6.1.3
# REMOVE: requests-unixsocket
```

### Phase 2: Simplify Initialization
```python
# services/log-aggregator/src/main.py
def __init__(self):
    # ... other init code ...
    
    # Initialize Docker client (simplified)
    try:
        self.docker_client = docker.from_env()
        self.docker_client.ping()
        logger.info("✅ Docker client initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Docker client: {e}")
        logger.debug("Check that /var/run/docker.sock is mounted and accessible")
        self.docker_client = None
```

### Phase 3: Test & Validate
1. Rebuild container with new dependencies
2. Verify socket connection works
3. Test log collection from running containers
4. Validate no permission errors

---

## Alternative Approaches (If socket still fails)

### Option A: Use Docker API via HTTP (less secure)
```python
# Only if Unix socket absolutely fails
client = docker.DockerClient(base_url='tcp://localhost:2375')
```

### Option B: Use docker CLI wrapper (simpler)
```python
import subprocess
logs = subprocess.check_output(['docker', 'logs', container_id])
```

### Option C: Use log driver integration (best for production)
- Configure JSON file logging driver
- Read logs directly from `/var/lib/docker/containers/*/container.log`
- No Docker API needed

---

## Expected Outcome

After implementing Phase 1-3:
```
✅ Docker client initialized successfully
✅ Collected 1247 log entries from 12 containers
💾 Stored 1247 logs in aggregation buffer
```

---

## Security Considerations

1. **Read-only socket mount** - Prevents container from modifying Docker
2. **Non-root user** - Runs as UID 1001, not root
3. **Group-based access** - Uses group_add for minimal privilege
4. **No privileged mode** - Not needed with proper group access

---

## Testing Checklist

- [ ] Update requirements.txt to docker==7.1.0
- [ ] Remove requests-unixsocket dependency
- [ ] Simplify Docker client initialization
- [ ] Rebuild container image
- [ ] Verify no "http+docker" errors in logs
- [ ] Test log collection from sample container
- [ ] Verify performance (< 1s to collect 1000 logs)
- [ ] Validate memory usage (< 128MB)

---

## References

- **Context7 Docker SDK Docs**: /docker/docker-py
- **Docker SDK GitHub**: https://github.com/docker/docker-py
- **urllib3 v2 Migration**: https://urllib3.readthedocs.io/en/stable/v2-migration-guide.html
- **Docker Socket Security**: https://docs.docker.com/engine/security/


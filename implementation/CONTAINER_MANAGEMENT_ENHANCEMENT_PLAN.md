# Container Management Enhancement Plan
## HA Ingestor Dashboard - Docker Integration

**Date:** October 13, 2025  
**Status:** Ready for Implementation  
**Priority:** High  
**Estimated Effort:** 4-6 hours  

---

## 🎯 Objectives

Based on your Docker Desktop screenshot and requirements:

1. **Enable containers to start without API keys** (they should start in "limited" mode)
2. **Add container start/stop functionality** to the dashboard UI
3. **Add API key management** for each external service
4. **Integrate Docker management** into the existing health dashboard

---

## 📊 Current State Analysis

### ✅ What's Already Working
- **Services Tab:** Shows service status and basic controls
- **Configuration Tab:** Has basic configuration management
- **Admin API:** Has health monitoring and configuration endpoints
- **Service Control:** Has restart functionality (but not start/stop)

### ❌ What's Missing
- **Container start/stop controls** (only restart exists)
- **API key management UI** for external services
- **Docker integration** in admin API
- **Service status** doesn't distinguish between "stopped" and "needs API key"

---

## 🏗️ Implementation Plan

### Phase 1: Backend - Docker Integration (2 hours)

#### 1.1 Add Docker Management to Admin API

**New Endpoints Needed:**
```python
# services/admin-api/src/docker_endpoints.py

@router.get("/containers")
async def list_containers():
    """List all Docker containers with status"""

@router.post("/containers/{container_name}/start")
async def start_container(container_name: str):
    """Start a Docker container"""

@router.post("/containers/{container_name}/stop") 
async def stop_container(container_name: str):
    """Stop a Docker container"""

@router.post("/containers/{container_name}/restart")
async def restart_container(container_name: str):
    """Restart a Docker container"""

@router.get("/containers/{container_name}/logs")
async def get_container_logs(container_name: str):
    """Get container logs"""

@router.get("/api-keys")
async def get_api_keys():
    """Get current API key configuration"""

@router.put("/api-keys/{service}")
async def update_api_key(service: str, api_key: str):
    """Update API key for a service"""
```

#### 1.2 Docker Integration Service

**Create:** `services/admin-api/src/docker_service.py`
```python
import docker
import os
from typing import List, Dict, Optional

class DockerService:
    def __init__(self):
        self.client = docker.from_env()
        self.container_mapping = {
            'websocket-ingestion': 'homeiq-websocket',
            'enrichment-pipeline': 'homeiq-enrichment', 
            'admin-api': 'homeiq-admin',
            'health-dashboard': 'homeiq-dashboard',
            'influxdb': 'homeiq-influxdb',
            'weather-api': 'homeiq-weather',
            'carbon-intensity-service': 'homeiq-carbon-intensity',
            'electricity-pricing-service': 'homeiq-electricity-pricing',
            'air-quality-service': 'homeiq-air-quality',
            'calendar-service': 'homeiq-calendar',
            'smart-meter-service': 'homeiq-smart-meter',
            'data-retention': 'homeiq-data-retention'
        }
    
    async def list_containers(self) -> List[Dict]:
        """List all project containers with status"""
        
    async def start_container(self, service_name: str) -> bool:
        """Start a container"""
        
    async def stop_container(self, service_name: str) -> bool:
        """Stop a container"""
        
    async def restart_container(self, service_name: str) -> bool:
        """Restart a container"""
        
    async def get_container_logs(self, service_name: str) -> str:
        """Get container logs"""
```

#### 1.3 API Key Management Service

**Create:** `services/admin-api/src/api_key_service.py`
```python
class APIKeyService:
    def __init__(self):
        self.config_file = "/app/infrastructure/.env.production"
        self.api_keys = {
            'weather': 'WEATHER_API_KEY',
            'carbon-intensity': 'WATTTIME_API_TOKEN', 
            'electricity-pricing': 'PRICING_API_KEY',
            'air-quality': 'AIRNOW_API_KEY',
            'calendar': 'GOOGLE_CLIENT_SECRET',
            'smart-meter': 'METER_API_TOKEN'
        }
    
    async def get_api_keys(self) -> Dict[str, str]:
        """Get masked API keys"""
        
    async def update_api_key(self, service: str, key: str) -> bool:
        """Update API key in environment"""
        
    async def test_api_key(self, service: str, key: str) -> bool:
        """Test if API key works"""
```

### Phase 2: Frontend - Enhanced UI (2-3 hours)

#### 2.1 Enhanced Services Tab

**Update:** `services/health-dashboard/src/components/ServicesTab.tsx`

**New Features:**
- **Start/Stop buttons** instead of just restart
- **API key status indicators** (🔑 Required, ✅ Configured, ❌ Invalid)
- **Service-specific actions** based on type
- **Real-time status updates** with container state

**Enhanced Service Cards:**
```tsx
interface EnhancedServiceCardProps {
  service: ServiceStatus;
  containerStatus: ContainerStatus;
  apiKeyStatus: APIKeyStatus;
  onStart: () => void;
  onStop: () => void;
  onConfigure: () => void;
}
```

#### 2.2 Container Management Component

**Create:** `services/health-dashboard/src/components/ContainerManagement.tsx`

**Features:**
- **Container status grid** (like Docker Desktop)
- **Bulk operations** (start all, stop all)
- **Container logs viewer**
- **Resource usage display**

#### 2.3 API Key Management Component

**Create:** `services/health-dashboard/src/components/APIKeyManagement.tsx`

**Features:**
- **API key configuration forms** for each service
- **Key validation** and testing
- **Masked/unmasked display**
- **Status indicators**

#### 2.4 Enhanced Configuration Tab

**Update:** `services/health-dashboard/src/components/tabs/ConfigurationTab.tsx`

**New Sections:**
- **Container Management** section
- **API Key Management** section  
- **Service Configuration** section (existing)

---

## 🎨 UI/UX Design

### Container Status Indicators

| Status | Icon | Color | Action Available |
|--------|------|-------|------------------|
| Running | 🟢 | Green | Stop, Restart |
| Stopped | 🔴 | Red | Start |
| Starting | 🟡 | Yellow | None |
| Stopping | 🟡 | Yellow | None |
| Error | ⚠️ | Red | Start, View Logs |

### API Key Status Indicators

| Status | Icon | Description |
|--------|------|-------------|
| ✅ Configured | 🔑 | API key set and valid |
| ❌ Invalid | 🔑❌ | API key set but invalid |
| ⚠️ Required | 🔑? | API key needed |
| 🚫 Disabled | 🔑🚫 | Service disabled |

### Enhanced Service Cards

```
┌─────────────────────────────────┐
│ 🌱 Carbon Intensity Service     │
│                                 │
│ Status: 🔴 Stopped              │
│ API Key: ⚠️ Required            │
│                                 │
│ [▶️ Start] [⚙️ Configure]       │
│ [📋 Logs] [📊 Details]          │
└─────────────────────────────────┘
```

---

## 📋 Implementation Checklist

### Backend Tasks
- [ ] Add `docker` dependency to admin-api requirements
- [ ] Create `DockerService` class
- [ ] Create `APIKeyService` class  
- [ ] Add Docker management endpoints
- [ ] Add API key management endpoints
- [ ] Update admin API main.py to include new routes
- [ ] Test Docker integration

### Frontend Tasks
- [ ] Update `ServicesTab` with start/stop controls
- [ ] Create `ContainerManagement` component
- [ ] Create `APIKeyManagement` component
- [ ] Update `ConfigurationTab` with new sections
- [ ] Add API service methods for Docker management
- [ ] Add API service methods for API key management
- [ ] Update TypeScript types
- [ ] Test UI components

### Integration Tasks
- [ ] Update Docker Compose to expose Docker socket to admin-api
- [ ] Add environment variables for API key management
- [ ] Update health checks to include container status
- [ ] Test end-to-end functionality

---

## 🔧 Technical Details

### Docker Socket Access

**Add to admin-api in docker-compose.yml:**
```yaml
admin-api:
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro
  environment:
    - DOCKER_HOST=unix:///var/run/docker.sock
```

### API Key Storage

**Environment-based storage:**
```bash
# /app/infrastructure/.env.production
WEATHER_API_KEY=your_key_here
WATTTIME_API_TOKEN=your_token_here
PRICING_API_KEY=your_key_here
# ... etc
```

### Container Name Mapping

**Service to Container Name:**
```python
CONTAINER_MAPPING = {
    'websocket-ingestion': 'homeiq-websocket',
    'enrichment-pipeline': 'homeiq-enrichment',
    'admin-api': 'homeiq-admin',
    'health-dashboard': 'homeiq-dashboard',
    'influxdb': 'homeiq-influxdb',
    'weather-api': 'homeiq-weather',
    'carbon-intensity-service': 'homeiq-carbon-intensity',
    'electricity-pricing-service': 'homeiq-electricity-pricing',
    'air-quality-service': 'homeiq-air-quality',
    'calendar-service': 'homeiq-calendar',
    'smart-meter-service': 'homeiq-smart-meter',
    'data-retention': 'homeiq-data-retention'
}
```

---

## 🚀 User Experience Flow

### Starting a Service Without API Key

1. **User clicks "Start"** on stopped service
2. **Container starts** in "limited" mode (no external API calls)
3. **Service shows** 🔴 Running, ⚠️ API Key Required
4. **User clicks "Configure"** to set API key
5. **User enters API key** and clicks "Test & Save"
6. **Service validates** API key and updates status
7. **Service automatically** begins full operation

### Managing Multiple Services

1. **User opens Services tab**
2. **Sees grid** of all services with status
3. **Can start/stop** individual services
4. **Can configure** API keys for external services
5. **Can view logs** for troubleshooting
6. **Can restart** services that need it

---

## 🔒 Security Considerations

### Docker Socket Access
- **Read-only access** to Docker socket
- **Limited permissions** for container operations
- **No privileged operations** (no container creation/deletion)

### API Key Management
- **Masked display** in UI (show only last 4 characters)
- **Secure storage** in environment files
- **Validation** before saving
- **No logging** of API keys

### Access Control
- **Local access only** (no external exposure)
- **Simple authentication** (existing admin API auth)
- **Audit logging** for container operations

---

## 📊 Success Metrics

### Functional Requirements
- [ ] All containers can be started without API keys
- [ ] All containers can be stopped/started from UI
- [ ] API keys can be configured through UI
- [ ] Service status reflects both container and API key state
- [ ] Container logs are accessible from UI

### Performance Requirements
- [ ] Container operations complete within 10 seconds
- [ ] UI updates within 2 seconds of container state change
- [ ] API key validation completes within 5 seconds
- [ ] No impact on existing dashboard performance

### User Experience Requirements
- [ ] Intuitive start/stop/configure workflow
- [ ] Clear status indicators for all states
- [ ] Helpful error messages for failed operations
- [ ] Consistent with existing dashboard design

---

## 🎯 Implementation Priority

### High Priority (Must Have)
1. **Container start/stop functionality**
2. **API key management UI**
3. **Service status integration**
4. **Basic error handling**

### Medium Priority (Should Have)
1. **Container logs viewer**
2. **Bulk operations**
3. **API key validation**
4. **Enhanced status indicators**

### Low Priority (Nice to Have)
1. **Container resource monitoring**
2. **Advanced logging features**
3. **Service dependency visualization**
4. **Automated health checks**

---

## 📝 Next Steps

1. **Review and approve** this plan
2. **Implement Phase 1** (Backend Docker integration)
3. **Test backend** functionality
4. **Implement Phase 2** (Frontend enhancements)
5. **Integration testing**
6. **User acceptance testing**

---

## 🤔 Questions for Consideration

1. **Scope:** Should we include container resource monitoring (CPU, memory)?
2. **Security:** Any additional security requirements for Docker access?
3. **UI:** Preference for modal dialogs vs. dedicated pages for configuration?
4. **Logs:** How much log history should we display?
5. **Validation:** Should API key validation be real-time or on-demand?

---

**Ready to implement when you approve this plan!** 🚀

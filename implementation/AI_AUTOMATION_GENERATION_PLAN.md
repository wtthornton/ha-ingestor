# AI Automation Generation Implementation Plan

**Epic:** AI1 - AI-Powered Automation Suggestions  
**Feature:** Dynamic Automation Generation with Approval Workflow  
**Date:** October 16, 2025  
**Status:** Planning Phase

---

## Executive Summary

Enable the `ai-automation-service` to generate Home Assistant automations dynamically based on user patterns and requests, with a secure approval workflow that leverages existing project infrastructure.

**Key Insight:** Home Assistant's OpenAI agent can generate YAML but cannot save automations natively. Our solution provides the missing middleware layer with approval, rollback, and audit capabilities.

---

## Architecture Overview

```
User Request → ai-automation-service (Generate YAML)
    ↓
SQLite Storage (pending_automations table)
    ↓
health-dashboard (Approval UI - new tab)
    ↓
data-api (Automation Management Endpoint)
    ↓
Home Assistant REST API (/api/config/automation/create)
    ↓
Audit Trail + Rollback Support
```

---

## Phase 1: Foundation - Data Layer (Week 1)

### 1.1 Extend ai-automation-service Database

**File:** `services/ai-automation-service/src/database.py`

```python
# Add new tables to existing SQLite database
class PendingAutomation(Base):
    __tablename__ = 'pending_automations'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    generated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    yaml_content: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(String(500))
    trigger_pattern: Mapped[str] = mapped_column(String(200))
    confidence_score: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20))  # pending, approved, rejected, active
    approved_by: Mapped[Optional[str]] = mapped_column(String(100))
    approved_at: Mapped[Optional[datetime]]
    ha_automation_id: Mapped[Optional[str]] = mapped_column(String(100))
    
class AutomationAudit(Base):
    __tablename__ = 'automation_audit'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    automation_id: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(50))  # created, modified, deleted, rolled_back
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    yaml_snapshot: Mapped[str] = mapped_column(Text)
    user: Mapped[str] = mapped_column(String(100))
    reason: Mapped[Optional[str]] = mapped_column(Text)
```

**Migration:** `services/ai-automation-service/alembic/versions/002_add_automation_tables.py`

**Tasks:**
- [ ] Create SQLAlchemy models
- [ ] Generate Alembic migration
- [ ] Add database initialization to startup
- [ ] Create CRUD operations for pending automations
- [ ] Add audit logging utilities

**Testing:**
- Unit tests for CRUD operations
- Migration rollback/forward tests
- Concurrent access tests (WAL mode)

---

## Phase 2: AI Generation Engine (Week 1-2)

### 2.1 Automation Generator Service

**File:** `services/ai-automation-service/src/automation_generator.py`

```python
class AutomationGenerator:
    """
    Generates HA automation YAML from patterns and context
    Uses data-api for rich device/entity/event context
    """
    
    async def generate_from_pattern(
        self,
        pattern: DevicePattern,
        context: AutomationContext
    ) -> GeneratedAutomation:
        """
        Generate automation YAML from detected pattern
        
        Args:
            pattern: Detected device usage pattern
            context: Device/entity metadata from data-api
            
        Returns:
            GeneratedAutomation with YAML, description, confidence
        """
        
    async def generate_from_request(
        self,
        user_request: str,
        available_devices: list[Device]
    ) -> GeneratedAutomation:
        """
        Generate automation from natural language request
        
        Uses OpenAI to convert request → structured automation
        """
        
    def validate_yaml(self, yaml_content: str) -> ValidationResult:
        """Validate automation YAML structure and safety"""
        
    async def get_automation_context(self) -> AutomationContext:
        """Fetch device/entity/event data from data-api"""
```

**Key Features:**
- Pattern-based generation (from existing pattern detection)
- Natural language request handling
- YAML validation (structure, required fields, safety checks)
- Context enrichment from data-api
- Confidence scoring

**Tasks:**
- [ ] Implement pattern → YAML converter
- [ ] Add OpenAI integration for NL requests
- [ ] Create YAML validator with safety rules
- [ ] Build context fetcher (data-api client)
- [ ] Add confidence scoring algorithm
- [ ] Implement template library for common patterns

**Testing:**
- Test pattern → YAML conversion accuracy
- Validate YAML structure compliance
- Test safety rules (no destructive actions without confirmation)
- Mock OpenAI responses for unit tests

---

## Phase 3: Data-API Extension (Week 2)

### 3.1 Automation Context Endpoint

**File:** `services/data-api/src/automation_endpoints.py`

```python
@router.get("/api/v1/automations/context")
async def get_automation_context(
    include_devices: bool = True,
    include_entities: bool = True,
    include_recent_events: bool = True,
    time_window_hours: int = 24
) -> AutomationContext:
    """
    Provide rich context for automation generation
    
    Returns:
        - Available devices and capabilities
        - Entity states and attributes
        - Recent event patterns
        - Frequently used device combinations
        - Time-based usage patterns
    """
    
@router.get("/api/v1/automations/pending")
async def list_pending_automations(
    status: Optional[str] = None
) -> list[PendingAutomation]:
    """List pending automations awaiting approval"""
    
@router.post("/api/v1/automations/approve/{automation_id}")
async def approve_automation(
    automation_id: int,
    approved_by: str
) -> AutomationApprovalResult:
    """
    Approve pending automation and save to Home Assistant
    
    Flow:
        1. Validate automation still valid
        2. POST to HA REST API
        3. Update status to 'active'
        4. Create audit record
        5. Return result with HA automation ID
    """
    
@router.post("/api/v1/automations/reject/{automation_id}")
async def reject_automation(
    automation_id: int,
    reason: str
) -> dict:
    """Reject and archive pending automation"""
    
@router.post("/api/v1/automations/rollback/{automation_id}")
async def rollback_automation(
    automation_id: str,
    reason: str
) -> dict:
    """
    Rollback automation to previous state
    
    Uses audit trail to restore previous YAML version
    """
```

**Tasks:**
- [ ] Create automation context aggregation logic
- [ ] Implement HA REST API client for automation CRUD
- [ ] Add approval workflow endpoints
- [ ] Build rollback mechanism using audit trail
- [ ] Add rate limiting for HA API calls
- [ ] Implement error handling for HA API failures

**Testing:**
- Test context aggregation performance (<100ms)
- Mock HA REST API responses
- Test approval workflow state transitions
- Verify audit trail completeness
- Test rollback with various scenarios

---

## Phase 4: Dashboard UI - Approval Interface (Week 2-3)

### 4.1 New Tab: "AI Automations"

**File:** `services/health-dashboard/src/components/tabs/AIAutomationsTab.tsx`

```typescript
interface AIAutomationsTabProps {
  // Leverages existing useHealth and API patterns
}

export function AIAutomationsTab() {
  const [pendingAutomations, setPendingAutomations] = useState<PendingAutomation[]>([]);
  const [selectedAutomation, setSelectedAutomation] = useState<PendingAutomation | null>(null);
  
  return (
    <div className="space-y-6">
      {/* Pending Automations Queue */}
      <PendingAutomationsQueue
        automations={pendingAutomations}
        onSelect={setSelectedAutomation}
      />
      
      {/* Automation Preview & Approval */}
      <AutomationPreview
        automation={selectedAutomation}
        onApprove={handleApprove}
        onReject={handleReject}
      />
      
      {/* Active AI Automations */}
      <ActiveAutomationsList
        onRollback={handleRollback}
      />
      
      {/* Audit History */}
      <AutomationAuditLog />
    </div>
  );
}
```

**Components:**

1. **PendingAutomationsQueue**
   - Card-based list of pending automations
   - Confidence score badges (green/yellow/red)
   - Pattern description and trigger summary
   - Quick preview of YAML

2. **AutomationPreview**
   - Full YAML viewer with syntax highlighting
   - Side-by-side comparison with similar automations
   - Safety analysis (affected devices, potential conflicts)
   - Approve/Reject buttons with confirmation
   - Edit capability (modify YAML before approval)

3. **ActiveAutomationsList**
   - List of AI-generated automations currently active
   - Status indicators (enabled/disabled)
   - Performance metrics (trigger count, success rate)
   - Rollback button with reason input
   - Link to HA automation editor

4. **AutomationAuditLog**
   - Timeline of all automation actions
   - Filterable by action type, date, user
   - Expandable entries showing YAML diffs

**Tasks:**
- [ ] Create tab component structure
- [ ] Build pending automations queue UI
- [ ] Implement YAML preview with syntax highlighting
- [ ] Add approval/rejection flows
- [ ] Create active automations management UI
- [ ] Build audit log viewer
- [ ] Add real-time updates via WebSocket
- [ ] Implement inline YAML editor (optional)

**Testing:**
- Component unit tests (Vitest)
- User interaction flows (Playwright)
- Approval/rejection state management
- WebSocket real-time updates

---

## Phase 5: Home Assistant Integration (Week 3)

### 5.1 HA REST API Client

**File:** `services/data-api/src/clients/ha_automation_client.py`

```python
class HAAutomationClient:
    """Client for Home Assistant automation CRUD operations"""
    
    def __init__(self, ha_url: str, ha_token: str):
        self.ha_url = ha_url
        self.ha_token = ha_token
        self.session = aiohttp.ClientSession()
        
    async def create_automation(
        self,
        automation_yaml: str
    ) -> HAAutomationResponse:
        """
        POST to /api/config/automation/config/{automation_id}
        
        Returns:
            automation_id, status, errors
        """
        
    async def get_automation(
        self,
        automation_id: str
    ) -> dict:
        """GET automation configuration"""
        
    async def update_automation(
        self,
        automation_id: str,
        automation_yaml: str
    ) -> HAAutomationResponse:
        """UPDATE existing automation"""
        
    async def delete_automation(
        self,
        automation_id: str
    ) -> dict:
        """DELETE automation"""
        
    async def trigger_automation(
        self,
        automation_id: str
    ) -> dict:
        """Manually trigger automation for testing"""
        
    async def validate_connection(self) -> bool:
        """Validate HA connection and permissions"""
```

**Configuration:**
- Add to `infrastructure/env.data-api`:
  ```bash
  HA_AUTOMATION_API_URL=http://homeassistant:8123/api
  HA_AUTOMATION_TOKEN=<long-lived-token>
  HA_AUTOMATION_ENABLED=true
  ```

**Tasks:**
- [ ] Implement HA REST API client
- [ ] Add authentication handling
- [ ] Implement retry logic with exponential backoff
- [ ] Add comprehensive error handling
- [ ] Create connection health check
- [ ] Add rate limiting (respect HA API limits)
- [ ] Implement response validation

**Testing:**
- Mock HA API responses
- Test error scenarios (network, auth, rate limit)
- Verify retry logic
- Test connection health checks

---

## Phase 6: MQTT Command Channel (Optional - Week 4)

### 6.1 Bi-Directional MQTT Flow

**Purpose:** Enable HA-side approval workflow for users who prefer native HA UI

```
ai-automation-service → MQTT Publish
    Topic: homeiq/automation/proposed
    Payload: {automation_id, yaml, description}
    ↓
Home Assistant MQTT Automation (user creates)
    Trigger: MQTT message received
    Action: Display notification with approve/reject buttons
    ↓
User clicks approve → HA publishes to MQTT
    Topic: homeiq/automation/approved
    Payload: {automation_id, approved_by}
    ↓
ai-automation-service → MQTT Subscribe
    Receives approval → Creates automation via REST API
```

**Tasks:**
- [ ] Add MQTT publisher to ai-automation-service
- [ ] Create MQTT subscriber for approvals
- [ ] Document HA MQTT automation setup
- [ ] Add MQTT fallback for REST API failures
- [ ] Create sample HA MQTT automations

**Testing:**
- Test MQTT message flow
- Verify message delivery and persistence
- Test concurrent approval requests

---

## Phase 7: Safety & Validation (Ongoing)

### 7.1 Safety Rules Engine

**File:** `services/ai-automation-service/src/safety_validator.py`

```python
class SafetyValidator:
    """Validates automation safety before allowing save"""
    
    RULES = [
        # Destructive actions require explicit confirmation
        "no_climate_extreme_changes",  # No >5°F changes
        "no_bulk_device_off",  # No "turn off all" without confirmation
        "no_security_disable",  # Never disable security automations
        "no_conflicting_automations",  # Check for conflicts
        "require_time_constraints",  # Encourage time/condition bounds
        "no_excessive_triggers",  # Warn on high-frequency triggers
    ]
    
    def validate(self, yaml_content: str) -> SafetyResult:
        """Run all safety checks"""
        
    def check_conflicts(
        self,
        new_automation: dict,
        existing_automations: list[dict]
    ) -> list[Conflict]:
        """Detect potential conflicts with existing automations"""
```

**Tasks:**
- [ ] Implement safety rule checks
- [ ] Create conflict detection algorithm
- [ ] Add configurable safety levels (strict/moderate/permissive)
- [ ] Build safety report for approval UI
- [ ] Add override mechanism for power users

**Testing:**
- Test each safety rule independently
- Test conflict detection accuracy
- Verify override mechanism works
- Test edge cases and false positives

---

## Phase 8: Integration & E2E Testing (Week 4)

### 8.1 End-to-End Test Scenarios

**Test Suite:** Playwright tests in `tests/e2e/ai-automations.spec.ts`

1. **Happy Path: Pattern-Based Generation**
   - Service detects pattern (light always on at 7pm)
   - Generates automation proposal
   - User approves via dashboard
   - Automation created in HA
   - Verify audit trail

2. **Natural Language Request**
   - User submits: "Turn off heater when window opens"
   - AI generates YAML
   - User previews and approves
   - Automation saved and active

3. **Rejection Flow**
   - User rejects automation with reason
   - Automation archived
   - Verify status updates

4. **Rollback Scenario**
   - Automation misbehaves
   - User clicks rollback
   - Previous version restored
   - Audit trail updated

5. **Safety Validation**
   - AI generates unsafe automation (turn off all security)
   - Safety validator flags it
   - User sees warning
   - Approval requires explicit confirmation

6. **Conflict Detection**
   - New automation conflicts with existing
   - Dashboard shows conflict warning
   - User resolves conflict

**Tasks:**
- [ ] Create E2E test suite
- [ ] Add mock HA API for testing
- [ ] Test all approval workflows
- [ ] Verify real-time updates
- [ ] Test error scenarios
- [ ] Performance testing (>100 pending automations)

---

## Database Schema Summary

```sql
-- ai-automation-service database

CREATE TABLE pending_automations (
    id INTEGER PRIMARY KEY,
    generated_at DATETIME NOT NULL,
    yaml_content TEXT NOT NULL,
    description VARCHAR(500) NOT NULL,
    trigger_pattern VARCHAR(200),
    confidence_score FLOAT NOT NULL,
    status VARCHAR(20) NOT NULL,  -- pending, approved, rejected, active
    approved_by VARCHAR(100),
    approved_at DATETIME,
    ha_automation_id VARCHAR(100)
);

CREATE TABLE automation_audit (
    id INTEGER PRIMARY KEY,
    automation_id VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,  -- created, modified, deleted, rolled_back
    timestamp DATETIME NOT NULL,
    yaml_snapshot TEXT NOT NULL,
    user VARCHAR(100) NOT NULL,
    reason TEXT
);

CREATE INDEX idx_pending_status ON pending_automations(status);
CREATE INDEX idx_audit_automation ON automation_audit(automation_id);
CREATE INDEX idx_audit_timestamp ON automation_audit(timestamp);
```

---

## API Endpoints Summary

### ai-automation-service
- `POST /api/v1/ai/generate-from-pattern` - Generate from detected pattern
- `POST /api/v1/ai/generate-from-request` - Generate from NL request
- `GET /api/v1/ai/pending` - List pending automations
- `GET /api/v1/ai/pending/{id}` - Get automation details

### data-api (new endpoints)
- `GET /api/v1/automations/context` - Get automation generation context
- `GET /api/v1/automations/pending` - List pending automations
- `POST /api/v1/automations/approve/{id}` - Approve automation
- `POST /api/v1/automations/reject/{id}` - Reject automation
- `POST /api/v1/automations/rollback/{id}` - Rollback automation
- `GET /api/v1/automations/audit` - Get audit history

---

## Configuration Files

### `infrastructure/env.ai-automation`
```bash
# Existing config...
AI_AUTOMATION_DATABASE_PATH=data/ai_automations.db

# New additions
AI_AUTOMATION_GENERATION_ENABLED=true
AI_AUTOMATION_APPROVAL_REQUIRED=true
AI_AUTOMATION_SAFETY_LEVEL=moderate  # strict, moderate, permissive
AI_AUTOMATION_MAX_PENDING=50
```

### `infrastructure/env.data-api`
```bash
# Existing config...

# New additions for HA automation management
HA_AUTOMATION_API_URL=http://homeassistant:8123/api
HA_AUTOMATION_TOKEN=${HA_LONG_LIVED_TOKEN}
HA_AUTOMATION_ENABLED=true
HA_AUTOMATION_RATE_LIMIT=10  # requests per minute
```

---

## Documentation Updates

### User Documentation
- **File:** `docs/AI_AUTOMATION_USER_GUIDE.md`
  - How to review and approve automations
  - Understanding confidence scores
  - Safety rules and overrides
  - Rollback procedures
  - Best practices

### Technical Documentation
- **File:** `docs/architecture/ai-automation-generation.md`
  - Architecture diagram
  - Data flow
  - API specifications
  - Safety validation logic
  - Audit trail design

### Deployment Guide
- **File:** `docs/DEPLOYMENT_GUIDE.md` (update)
  - Add HA long-lived token setup
  - Configure automation API access
  - Enable MQTT (if using optional Phase 6)

---

## Success Metrics

### Technical Metrics
- [ ] Generation latency <500ms
- [ ] Approval → HA save <1s
- [ ] YAML validation accuracy >99%
- [ ] Safety rule false positive rate <5%
- [ ] Conflict detection accuracy >95%

### User Experience Metrics
- [ ] Automation approval rate >70%
- [ ] Rollback rate <5%
- [ ] Average review time <2 minutes
- [ ] User satisfaction score >4/5

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| HA API rate limiting | High | Implement queue with backoff, cache responses |
| Invalid YAML crashes HA | Critical | Multi-layer validation, safety sandbox testing |
| Conflicting automations | Medium | Conflict detection, user warnings |
| AI generates unsafe automation | High | Safety validator, approval workflow, audit trail |
| Performance degradation | Medium | Database indexing, pagination, caching |
| User overwhelmed by suggestions | Low | Configurable frequency, batch by similarity |

---

## Timeline Summary

- **Week 1:** Foundation (Database, AI Engine) - 40 hours
- **Week 2:** API Layer (data-api endpoints, HA client) - 40 hours
- **Week 3:** Dashboard UI (Approval interface) - 40 hours
- **Week 4:** Testing & Polish (E2E tests, safety validation) - 40 hours

**Total Estimated Effort:** 160 hours (4 weeks, 1 developer full-time)

---

## Next Steps

1. **Review and Approve Plan** - Stakeholder sign-off
2. **Create Epic and Stories** - Break down into BMAD stories
3. **Spike: HA REST API Testing** - Validate HA automation API access
4. **Phase 1 Kickoff** - Begin database schema implementation

---

## Questions for Discussion

1. Should we implement MQTT command channel (Phase 6) in initial release or defer?
2. What safety level should be default? (strict/moderate/permissive)
3. Do we want inline YAML editing in approval UI or force regeneration?
4. Should rollback be automatic on first failure or manual only?
5. Do we need multi-user approval for critical automations?

---

**Document Status:** Draft for Review  
**Last Updated:** October 16, 2025  
**Next Review:** After stakeholder feedback


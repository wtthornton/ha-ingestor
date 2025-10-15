# Source Tree Structure

This document defines the complete source tree structure for the Home Assistant Ingestor project, following BMAD framework standards and microservices architecture patterns.

## Root Directory Structure

```
ha-ingestor/
├── .bmad-core/                    # BMAD framework core files
│   ├── agents/                    # AI agent definitions
│   ├── tasks/                     # Task definitions
│   ├── templates/                 # Document templates
│   ├── checklists/                # Quality checklists
│   └── core-config.yaml           # BMAD configuration
├── .cursor/                       # Cursor IDE rules and configuration
│   └── rules/                     # AI agent rules
├── docs/                          # Project documentation (REFERENCE ONLY)
│   ├── architecture/              # Architecture documentation
│   ├── prd/                       # Product Requirements (sharded)
│   ├── stories/                   # Development stories
│   ├── qa/                        # Quality assurance documents
│   └── kb/                        # Knowledge base cache
├── implementation/                # Implementation notes and status (NOT docs)
│   ├── analysis/                  # Technical analysis and diagnosis
│   ├── verification/              # Test and verification results
│   └── archive/                   # Old/superseded implementation notes
├── services/                      # 13 Microservices (Alpine-based)
│   ├── admin-api/                 # System monitoring & control API (Port 8003) [Epic 13]
│   ├── data-api/                  # Feature data hub API (Port 8006) [Epic 13]
│   ├── health-dashboard/          # React frontend (12 tabs, Port 3000)
│   ├── websocket-ingestion/       # WebSocket client service (Port 8001)
│   ├── enrichment-pipeline/       # Data processing service (Port 8002)
│   ├── data-retention/            # Data lifecycle management (Port 8080)
│   ├── sports-data/               # ESPN sports API service (Port 8005) [SQLite webhooks - Epic 22.3]
│   ├── log-aggregator/            # Centralized logging (Port 8015)
│   ├── weather-api/               # Weather integration (Internal)
│   ├── carbon-intensity-service/  # Carbon data (Port 8010)
│   ├── electricity-pricing-service/ # Pricing data (Port 8011)
│   ├── air-quality-service/       # Air quality (Port 8012)
│   ├── calendar-service/          # Calendar integration (Port 8013)
│   ├── smart-meter-service/       # Smart meter (Port 8014)
│   └── ha-simulator/              # Test event generator
├── shared/                        # Shared Python utilities
│   ├── logging_config.py          # ⭐ Structured logging + correlation IDs
│   ├── correlation_middleware.py # Request tracking middleware
│   ├── metrics_collector.py       # Metrics collection framework
│   ├── alert_manager.py           # Alert management system
│   ├── system_metrics.py          # System-level metrics
│   └── types/                     # Shared type definitions
│       └── health.py              # Health status types
├── infrastructure/                # Infrastructure configuration
│   ├── docker-logging.conf        # Docker logging configuration
│   ├── env.example                # Environment template
│   ├── env.production             # Production environment
│   ├── .env.websocket             # WebSocket service config
│   ├── .env.weather               # Weather API config
│   ├── .env.influxdb              # InfluxDB config
│   ├── env.sports.template        # Sports API template
│   └── influxdb/                  # InfluxDB configuration
│       ├── influxdb.conf          # InfluxDB server config
│       └── init-influxdb.sh       # Initialization script
├── scripts/                       # Deployment and utility scripts
├── tests/                         # Integration and E2E tests (Playwright)
├── tools/cli/                     # CLI utilities and helpers
├── docker-compose.yml             # Main Docker Compose (Production)
├── docker-compose.dev.yml         # Development with hot reload
├── docker-compose.prod.yml        # Production overrides
├── docker-compose.minimal.yml     # Core services only
├── docker-compose.simple.yml      # Simplified configuration
└── README.md                      # Project overview (Updated)
```

## Services Directory Structure

> **Epic 13 Note**: The API layer was separated into two services:
> - **admin-api (8003)** → System monitoring, health checks, Docker management
> - **data-api (8006)** → Feature data queries (events, devices, sports, analytics)
> 
> This separation improves scalability and allows independent scaling of monitoring vs data access layers.

### Admin API Service (`services/admin-api/`) [Epic 13]
**Purpose:** System monitoring and control
**Port:** 8003

```
admin-api/
├── src/
│   ├── main.py                    # FastAPI application entry point
│   ├── auth.py                    # Authentication and authorization
│   ├── health_endpoints.py        # Health check endpoints (Epic 17.2)
│   ├── stats_endpoints.py         # Statistics endpoints
│   ├── config_endpoints.py        # Configuration endpoints
│   ├── docker_endpoints.py        # Docker management (Epic 13 Story 13.1)
│   ├── monitoring_endpoints.py    # Monitoring endpoints (Epic 17.3)
│   ├── websocket_endpoints.py     # WebSocket endpoints
│   ├── logging_service.py         # Logging service
│   ├── metrics_service.py         # Metrics collection (Epic 17.4)
│   ├── alerting_service.py        # Alert management (Epic 17.4)
│   ├── events_endpoints.py        # Events endpoints (DEPRECATED - moved to data-api)
│   └── devices_endpoints.py       # Devices endpoints (DEPRECATED - moved to data-api)
├── tests/                         # Service-specific tests
├── Dockerfile                     # Production Docker image
├── Dockerfile.dev                 # Development Docker image
└── requirements.txt               # Python dependencies
```

### Data API Service (`services/data-api/`) [Epic 13 NEW]
**Purpose:** Feature data hub for events, devices, sports, and analytics
**Port:** 8006
**Databases:** InfluxDB (time-series) + SQLite (metadata) [Epic 22]

```
data-api/
├── src/
│   ├── main.py                    # FastAPI application entry point
│   ├── database.py                # SQLite async configuration (Epic 22.1)
│   ├── models/                    # SQLAlchemy models (Epic 22.2)
│   │   ├── __init__.py            # Model exports
│   │   ├── device.py              # Device model
│   │   └── entity.py              # Entity model
│   ├── events_endpoints.py        # Event queries (migrated from admin-api)
│   ├── devices_endpoints.py       # Device & entity browsing (Epic 22.2: SQLite)
│   ├── sports_endpoints.py        # Sports data queries (Epic 12 Story 12.2)
│   ├── ha_automation_endpoints.py # HA automation integration (Epic 12 Story 12.3)
│   ├── alert_endpoints.py         # Alert management (Epic 13 Story 13.3)
│   ├── metrics_endpoints.py       # Metrics endpoints (Epic 13 Story 13.3)
│   ├── integration_endpoints.py   # Integration management (Epic 13 Story 13.3)
│   ├── websocket_endpoints.py     # WebSocket streaming
│   ├── alerting_service.py        # Alerting service
│   ├── influxdb_client.py         # InfluxDB query client
│   └── metrics_service.py         # Metrics service
├── alembic/                       # Database migrations (Epic 22.1)
│   ├── env.py                     # Alembic environment
│   └── versions/                  # Migration scripts
├── tests/                         # Service-specific tests
│   ├── test_database.py           # SQLite tests (Epic 22.1)
│   └── test_models.py             # Model tests (Epic 22.2)
├── Dockerfile                     # Production Docker image
├── Dockerfile.dev                 # Development Docker image
├── alembic.ini                    # Alembic configuration
└── requirements.txt               # Python dependencies (includes SQLAlchemy)
```

**Epic 13 API Endpoints:**
- **Events:** `/events`, `/events/{id}`, `/events/search`, `/events/stats`
- **Devices:** `/api/devices`, `/api/devices/{id}`, `/api/entities`, `/api/entities/{id}`
- **Sports:** `/api/v1/sports/games/history`, `/api/v1/sports/games/timeline/{id}`, `/api/v1/sports/schedule/{team}`
- **HA Automation:** `/api/v1/ha/game-status/{team}`, `/api/v1/ha/game-context/{team}`, `/api/v1/ha/webhooks/*`
- **Integrations:** `/api/v1/integrations`, `/api/v1/services`
- **WebSocket:** `/ws` (real-time streaming)

### Health Dashboard Service (`services/health-dashboard/`)
```
health-dashboard/
├── src/
│   ├── components/                # React components
│   │   ├── Dashboard.tsx          # Main dashboard with 11 tabs
│   │   ├── tabs/                  # Tab components
│   │   │   ├── OverviewTab.tsx    # System overview
│   │   │   ├── ServicesTab.tsx    # Service management
│   │   │   ├── DependenciesTab.tsx # Dependency visualization
│   │   │   ├── DevicesTab.tsx     # Device & entity browser
│   │   │   ├── EventsTab.tsx      # Real-time event stream
│   │   │   ├── LogsTab.tsx        # Live log viewer
│   │   │   ├── SportsTab.tsx      # Sports tracking
│   │   │   ├── DataSourcesTab.tsx # Data sources status
│   │   │   ├── AnalyticsTab.tsx   # Performance analytics
│   │   │   ├── AlertsTab.tsx      # Alert management
│   │   │   └── ConfigurationTab.tsx # Service configuration
│   │   ├── ServiceDependencyGraph.tsx # ⭐ Interactive graph
│   │   ├── sports/                # Sports components
│   │   │   ├── LiveGameCard.tsx   # Live game display
│   │   │   ├── TeamSelector.tsx   # Team selection UI
│   │   │   └── SetupWizard.tsx    # First-run setup
│   │   ├── ConnectionStatusIndicator.tsx # WebSocket status
│   │   ├── AlertBanner.tsx        # Alert notifications
│   │   ├── MetricsChart.tsx       # Chart.js charts
│   │   └── widgets/               # Reusable widgets
│   ├── hooks/                     # Custom React hooks
│   │   ├── useRealtimeMetrics.ts  # WebSocket hook
│   │   ├── useHealth.ts           # Health status hook
│   │   └── useStatistics.ts       # Statistics hook
│   ├── services/                  # API service layer
│   │   ├── api.ts                 # API client
│   │   └── websocket.ts           # WebSocket service
│   ├── types/                     # TypeScript type definitions
│   ├── App.tsx                    # Main application
│   └── main.tsx                   # Entry point
├── tests/                         # Playwright E2E tests
├── public/                        # Static assets
├── Dockerfile                     # Production (nginx + multi-stage)
├── nginx.conf                     # nginx configuration
├── package.json                   # Dependencies
├── vite.config.ts                 # Vite build configuration
├── vitest.config.ts               # Vitest test configuration
├── playwright.config.ts           # Playwright E2E configuration
└── tailwind.config.js             # TailwindCSS configuration
```

### WebSocket Ingestion Service (`services/websocket-ingestion/`)
```
websocket-ingestion/
├── src/
│   ├── main.py                    # Service entry point
│   ├── connection_manager.py      # WebSocket connection management
│   ├── event_processor.py         # Event processing logic
│   ├── influxdb_wrapper.py        # InfluxDB integration
│   ├── weather_client.py          # Weather API client
│   ├── health_check.py            # Health check endpoint
│   ├── async_event_processor.py   # Async event processing
│   ├── batch_processor.py         # Batch processing
│   ├── memory_manager.py          # Memory management
│   └── error_handler.py           # Error handling
├── tests/                         # Service tests
├── Dockerfile                     # Production Docker image
├── Dockerfile.dev                 # Development Docker image
└── requirements.txt               # Python dependencies
```

### Enrichment Pipeline Service (`services/enrichment-pipeline/`)
```
enrichment-pipeline/
├── src/
│   ├── main.py                    # Service entry point
│   ├── data_normalizer.py         # Data normalization
│   ├── influxdb_wrapper.py        # InfluxDB client
│   ├── data_validator.py          # Data validation
│   ├── quality_metrics.py         # Quality metrics
│   ├── quality_alerts.py          # Quality alerts
│   ├── quality_dashboard.py       # Quality dashboard API
│   └── quality_reporting.py       # Quality reporting
├── tests/                         # Service tests
├── Dockerfile                     # Production Docker image
├── Dockerfile.dev                 # Development Docker image
└── requirements.txt               # Python dependencies
```

### Data Retention Service (`services/data-retention/`)
```
data-retention/
├── src/
│   ├── main.py                    # Service entry point
│   ├── retention_policy.py        # Data retention policies
│   ├── data_cleanup.py            # Data cleanup logic
│   ├── backup_restore.py          # Backup and restore
│   └── health_check.py            # Health check endpoint
├── tests/                         # Service tests
├── Dockerfile                     # Production Docker image
├── Dockerfile.dev                 # Development Docker image
├── requirements.txt               # Python dependencies
└── README.md                      # Service documentation
```

## Shared Directory Structure

### Shared Types (`shared/types/`)
```
types/
├── index.ts                       # Type exports
├── api.ts                         # API response types
├── health.ts                      # Health status types
├── events.ts                      # Event data types
├── statistics.ts                  # Statistics types
└── config.ts                      # Configuration types
```

### Shared Configuration (`shared/`)
```
shared/
├── logging_config.py              # Shared logging configuration
└── types/                         # Shared TypeScript types
```

## Infrastructure Directory Structure

### Infrastructure Configuration (`infrastructure/`)
```
infrastructure/
├── docker-logging.conf            # Docker logging configuration
├── env.example                    # Environment variables template
├── env.production                 # Production environment variables
└── influxdb/                      # InfluxDB configuration
    ├── influxdb.conf              # InfluxDB server configuration
    └── init-influxdb.sh           # InfluxDB initialization script
```

## Critical: docs/ vs implementation/

### Understanding the Difference

**`docs/` = Reference Documentation**
- **Purpose**: Permanent, reusable documentation for the project
- **Audience**: Developers, users, stakeholders (long-term reference)
- **Lifecycle**: Updated as project evolves, not tied to specific sessions
- **Examples**: Architecture docs, PRD, user guides, API documentation

**`implementation/` = Implementation Notes**
- **Purpose**: Session notes, status reports, and implementation artifacts
- **Audience**: Development team (short-term tracking)
- **Lifecycle**: Created during development, archived after completion
- **Examples**: Status reports, completion summaries, fix reports, analysis

### When to Use Each

| File Type | Location | Reason |
|-----------|----------|--------|
| Architecture documentation | `docs/architecture/` | Long-term reference |
| User manual | `docs/` | Permanent documentation |
| API documentation | `docs/` | Reference guide |
| Deployment guide | `docs/` | Reusable instructions |
| Status report | `implementation/` | Session artifact |
| Completion summary | `implementation/` | Implementation tracking |
| Fix report | `implementation/` | Development notes |
| Analysis/diagnosis | `implementation/analysis/` | Technical investigation |
| Verification results | `implementation/verification/` | Test results |

### Implementation Directory Structure

```
implementation/
├── analysis/                      # Technical analysis and diagnosis
│   ├── *_ANALYSIS.md             # System/API analysis
│   ├── *_DIAGNOSIS.md            # Problem diagnosis
│   └── *_CALL_TREE.md            # Code flow analysis
├── verification/                  # Test and verification results
│   ├── *_VERIFICATION_RESULTS.md # Test results
│   └── *_VERIFICATION.md         # Verification reports
├── archive/                       # Old/superseded notes
│   └── [dated folders]           # Organized by date/epic
├── *_COMPLETE.md                 # Completion reports
├── *_STATUS.md                   # Status reports
├── *_SUMMARY.md                  # Session summaries
├── *_PLAN.md                     # Implementation plans
├── *_FIX_*.md                    # Fix reports
└── EPIC_*_*.md                   # Epic-related notes
```

## Documentation Directory Structure

### Architecture Documentation (`docs/architecture/`)
```
architecture/
├── tech-stack.md                  # Technology stack definition
├── source-tree.md                 # Source tree structure (this file)
├── coding-standards.md            # Coding standards and conventions
├── data-models.md                 # Data model definitions
├── database-schema.md             # Database schema documentation
├── deployment-architecture.md     # Deployment architecture
├── development-workflow.md        # Development workflow
├── error-handling-strategy.md     # Error handling approach
├── monitoring-and-observability.md # Monitoring strategy
├── security-and-performance.md    # Security and performance guidelines
├── testing-strategy.md            # Testing approach
├── core-workflows.md              # Core workflow definitions
└── index.md                       # Architecture documentation index
```

### PRD Documentation (`docs/prd/`)
```
prd/
├── index.md                       # PRD main document
├── requirements.md                # Requirements definition
├── goals-and-background-context.md # Project goals and context
├── technical-assumptions.md       # Technical assumptions
├── user-interface-design-goals.md # UI/UX goals
├── epic-list.md                   # Epic list
├── epic-1-foundation-core-infrastructure.md # Epic 1
├── epic-2-data-capture-normalization.md # Epic 2
├── epic-3-data-enrichment-storage.md # Epic 3
├── epic-4-production-readiness-monitoring.md # Epic 4
├── epic-5-admin-interface-frontend.md # Epic 5
├── epic-6-critical-infrastructure-stabilization.md # Epic 6
├── next-steps.md                  # Next steps
└── checklist-results-report.md    # PRD checklist results
```

### Stories Documentation (`docs/stories/`)
```
stories/
├── [46 story files]               # Individual development stories
└── [Task files]                   # Specific task definitions
```

### QA Documentation (`docs/qa/`)
```
qa/
├── assessments/                   # Risk assessments
│   ├── [19 assessment files]      # Individual risk assessments
│   └── risk-assessment-summary-20241219.md # Risk summary
└── gates/                         # Quality gates
    ├── [27 gate files]            # Individual quality gates
    └── [Gate configuration files] # Gate definitions
```

## File Naming Conventions

### Services
- **Directories**: kebab-case (e.g., `admin-api`, `health-dashboard`)
- **Python files**: snake_case (e.g., `main.py`, `event_processor.py`)
- **TypeScript files**: camelCase (e.g., `Dashboard.tsx`, `useHealth.ts`)

### Documentation
- **Architecture docs**: kebab-case (e.g., `tech-stack.md`, `source-tree.md`)
- **Stories**: kebab-case with numbering (e.g., `1.1-project-setup-docker-infrastructure.md`)
- **QA gates**: kebab-case with epic.story format (e.g., `1.1-project-setup.yml`)

### Configuration
- **Environment files**: `.env`, `.env.example`, `.env.production`
- **Docker files**: `Dockerfile`, `Dockerfile.dev`, `docker-compose.yml`
- **Package files**: `package.json`, `requirements.txt`, `pyproject.toml`

## Import/Export Patterns

### Frontend (TypeScript/React)
```typescript
// Component imports
import { Dashboard } from './components/Dashboard'
import { useHealth } from './hooks/useHealth'

// Service imports
import { apiService } from './services/api'
import { websocketService } from './services/websocket'

// Type imports
import type { HealthStatus, EventData } from '../types'
```

### Backend (Python)
```python
# Service imports
from .auth import AuthManager
from .health_endpoints import HealthEndpoints

# Shared imports
from shared.logging_config import setup_logging
from shared.types import HealthStatus

# External imports
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
```

This source tree structure follows BMAD framework standards and provides clear organization for the Home Assistant Ingestor microservices architecture.

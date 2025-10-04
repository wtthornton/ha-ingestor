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
├── docs/                          # Project documentation
│   ├── architecture/              # Architecture documentation
│   ├── prd/                       # Product Requirements (sharded)
│   ├── stories/                   # Development stories
│   ├── qa/                        # Quality assurance documents
│   └── kb/                        # Knowledge base cache
├── services/                      # Microservices
│   ├── admin-api/                 # FastAPI REST API service
│   ├── health-dashboard/          # React frontend application
│   ├── websocket-ingestion/       # WebSocket client service
│   ├── enrichment-pipeline/       # Data processing service
│   ├── data-retention/            # Data cleanup service
│   └── weather-api/               # Weather integration service
├── shared/                        # Shared code and types
│   ├── types/                     # TypeScript interfaces
│   └── logging_config.py          # Shared logging configuration
├── infrastructure/                # Infrastructure configuration
│   ├── docker-logging.conf        # Docker logging configuration
│   ├── env.example                # Environment template
│   ├── env.production             # Production environment
│   └── influxdb/                  # InfluxDB configuration
├── scripts/                       # Deployment and utility scripts
├── tests/                         # Integration and E2E tests
├── tools/                         # CLI tools and utilities
├── docker-compose.yml             # Main Docker Compose file
├── docker-compose.dev.yml         # Development configuration
├── docker-compose.prod.yml        # Production configuration
└── README.md                      # Project overview
```

## Services Directory Structure

### Admin API Service (`services/admin-api/`)
```
admin-api/
├── src/
│   ├── main.py                    # FastAPI application entry point
│   ├── auth.py                    # Authentication and authorization
│   ├── health_endpoints.py        # Health check endpoints
│   ├── stats_endpoints.py         # Statistics endpoints
│   ├── config_endpoints.py        # Configuration endpoints
│   ├── events_endpoints.py        # Events endpoints
│   ├── monitoring_endpoints.py    # Monitoring endpoints
│   ├── websocket_endpoints.py     # WebSocket endpoints
│   ├── logging_service.py         # Logging service
│   ├── metrics_service.py         # Metrics collection
│   └── alerting_service.py        # Alert management
├── tests/                         # Service-specific tests
├── Dockerfile                     # Production Docker image
├── Dockerfile.dev                 # Development Docker image
└── requirements.txt               # Python dependencies
```

### Health Dashboard Service (`services/health-dashboard/`)
```
health-dashboard/
├── src/
│   ├── components/                # React components
│   │   ├── Dashboard.tsx          # Main dashboard component
│   │   ├── Navigation.tsx         # Navigation component
│   │   ├── StatusIndicator.tsx    # Status indicator
│   │   ├── Monitoring.tsx         # Monitoring component
│   │   ├── Settings.tsx           # Settings component
│   │   └── StatisticsCard.tsx     # Statistics display
│   ├── hooks/                     # Custom React hooks
│   │   ├── useHealth.ts           # Health status hook
│   │   ├── useStatistics.ts       # Statistics hook
│   │   └── useEvents.ts           # Events hook
│   ├── services/                  # API service layer
│   │   ├── api.ts                 # API client
│   │   ├── websocket.ts           # WebSocket service
│   │   └── notificationService.ts # Notification service
│   ├── contexts/                  # React contexts
│   │   ├── ThemeContext.tsx       # Theme management
│   │   ├── LayoutContext.tsx      # Layout management
│   │   └── NotificationContext.tsx # Notification management
│   ├── types/                     # TypeScript type definitions
│   │   └── index.ts               # Type exports
│   ├── utils/                     # Utility functions
│   │   └── exportUtils.ts         # Data export utilities
│   ├── App.tsx                    # Main application component
│   └── main.tsx                   # Application entry point
├── tests/                         # Component and unit tests
├── public/                        # Static assets
├── Dockerfile                     # Production Docker image
├── Dockerfile.dev                 # Development Docker image
├── package.json                   # Node.js dependencies
├── vite.config.ts                 # Vite configuration
├── tailwind.config.js             # TailwindCSS configuration
└── playwright.config.ts           # Playwright E2E configuration
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

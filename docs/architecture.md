# Home Assistant Ingestor - Architecture Documentation

## 📖 Overview

This document serves as the main entry point for the Home Assistant Ingestor architecture documentation.

**For complete architectural documentation, please see:** **[Architecture Documentation Index](architecture/index.md)**

---

## Quick Summary

**System Type:** Microservices-based real-time data ingestion system  
**Tech Stack:** Python 3.11, React 18.2, FastAPI, aiohttp, InfluxDB 2.7, Docker  
**Deployment:** Docker Compose with optimized Alpine images  
**Purpose:** Capture Home Assistant events, enrich with weather context, store in time-series database

## Architecture Diagram

```mermaid
graph TB
    HA[Home Assistant] -->|WebSocket| WS[WebSocket Ingestion<br/>Port: 8001]
    WS --> ENRICH[Enrichment Pipeline<br/>Port: 8002]
    ENRICH --> INFLUX[(InfluxDB 2.7<br/>Port: 8086)]
    
    DASH[Health Dashboard<br/>Port: 3000] -->|REST API| ADMIN[Admin API<br/>Port: 8003]
    ADMIN --> INFLUX
    
    WEATHER[Weather API<br/>Internal] --> ENRICH
    RETENTION[Data Retention<br/>Port: 8080] --> INFLUX
    
    subgraph "Docker Services"
        WS
        ENRICH
        ADMIN
        DASH
        WEATHER
        RETENTION
        INFLUX
    end
```

## Services

| Service | Technology | Port | Purpose |
|---------|-----------|------|---------|
| **websocket-ingestion** | Python/aiohttp | 8001 | Home Assistant WebSocket client |
| **enrichment-pipeline** | Python/FastAPI | 8002 | Data validation and weather enrichment |
| **data-retention** | Python/FastAPI | 8080 | Data lifecycle and cleanup management |
| **admin-api** | Python/FastAPI | 8003 | Administration REST API |
| **health-dashboard** | React/TypeScript | 3000 | Web-based monitoring interface |
| **weather-api** | Python/FastAPI | Internal | Weather data integration |
| **influxdb** | InfluxDB 2.7 | 8086 | Time-series data storage |

## 📚 Complete Documentation

For detailed architecture information, please refer to the comprehensive documentation in the `architecture/` directory:

### Getting Started
- **[Introduction](architecture/introduction.md)** - Project overview and high-level architecture
- **[Key Concepts](architecture/key-concepts.md)** - Core architectural concepts
- **[Tech Stack](architecture/tech-stack.md)** - Technology stack with rationale

### System Design
- **[Core Workflows](architecture/core-workflows.md)** - Data flow and sequence diagrams
- **[Deployment Architecture](architecture/deployment-architecture.md)** - Deployment patterns
- **[Source Tree](architecture/source-tree.md)** - Project structure
- **[Data Models](architecture/data-models.md)** - Data structures and types
- **[Database Schema](architecture/database-schema.md)** - InfluxDB schema design

### Development
- **[Development Workflow](architecture/development-workflow.md)** - Setup and contribution guide
- **[Coding Standards](architecture/coding-standards.md)** - Code quality standards
- **[Configuration Management](architecture/configuration-management.md)** - Environment configuration
- **[API Guidelines](architecture/api-guidelines.md)** - REST API design standards

### Quality & Operations
- **[Testing Strategy](architecture/testing-strategy.md)** - Testing approach
- **[Error Handling Strategy](architecture/error-handling-strategy.md)** - Error handling patterns
- **[Monitoring and Observability](architecture/monitoring-and-observability.md)** - Logging and metrics
- **[Performance Standards](architecture/performance-standards.md)** - Performance targets
- **[Security Standards](architecture/security-standards.md)** - Security best practices

### Full Index
📋 **[Complete Architecture Documentation Index](architecture/index.md)**

---

## Quick Development Reference

```bash
# Start all services
docker-compose up

# Frontend development (with hot reload)
cd services/health-dashboard && npm run dev

# Backend development (with auto-reload)
cd services/admin-api && python -m uvicorn src.main:app --reload

# Run tests
docker-compose -f docker-compose.yml run --rm websocket-ingestion pytest
cd services/health-dashboard && npm test
```

## Key Patterns

- **Microservices Architecture**: Independent, containerized services
- **Event-Driven Processing**: Real-time WebSocket event streaming
- **API Gateway Pattern**: FastAPI as unified REST interface
- **Service Isolation**: Docker containerization with health checks
- **Optimized Deployment**: Multi-stage Docker builds with Alpine Linux

## Performance Characteristics

- **Event Processing**: 10,000+ events/day
- **Response Time**: <100ms API calls
- **Reliability**: 99.9% uptime with auto-reconnection
- **Container Size**: 71% reduction with Alpine images (40-80MB per service)

---

**Last Updated**: October 2025  
**Version**: 4.0  
**Status**: Production Ready

**For complete details, see the [Architecture Documentation Index](architecture/index.md)**

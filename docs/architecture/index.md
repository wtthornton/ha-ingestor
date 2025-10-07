# Home Assistant Ingestor - Architecture Documentation Index

## Overview

This directory contains the comprehensive architectural documentation for the Home Assistant Ingestor system. This microservices-based real-time data ingestion platform captures Home Assistant events, enriches them with weather context, and stores them in InfluxDB for analysis.

## Quick Reference

**Technology Stack**: Python 3.11, React 18.2, FastAPI, aiohttp, InfluxDB 2.7, Docker  
**Deployment**: Docker Compose with optimized Alpine images  
**Architecture Style**: Microservices with event-driven processing  

## 📚 Architecture Documentation

### Getting Started

- **[Introduction](introduction.md)** - Project overview, goals, and high-level architecture
- **[Key Concepts](key-concepts.md)** - Core architectural concepts and design patterns
- **[Tech Stack](tech-stack.md)** - Complete technology stack with rationale and versions

### System Architecture

- **[Core Workflows](core-workflows.md)** - Primary system workflows and data flow diagrams
- **[Deployment Architecture](deployment-architecture.md)** - Deployment patterns and infrastructure setup
- **[Source Tree](source-tree.md)** - Project structure and file organization
- **[Data Models](data-models.md)** - Data structures and type definitions

### Development & Operations

- **[Development Workflow](development-workflow.md)** - Developer setup and contribution guide
- **[Coding Standards](coding-standards.md)** - Code quality standards and best practices
- **[Configuration Management](configuration-management.md)** - Environment and configuration guidelines
- **[API Guidelines](api-guidelines.md)** - REST API design standards and conventions

### Quality & Testing

- **[Testing Strategy](testing-strategy.md)** - Comprehensive testing approach (unit, integration, E2E)
- **[Error Handling Strategy](error-handling-strategy.md)** - Error handling patterns and recovery
- **[Monitoring and Observability](monitoring-and-observability.md)** - Logging, metrics, and alerting
- **[Performance Standards](performance-standards.md)** - Performance targets and optimization

### Security & Compliance

- **[Security Standards](security-standards.md)** - Security best practices and authentication
- **[Security and Performance](security-and-performance.md)** - Combined security and performance considerations
- **[Compliance Standard Framework](compliance-standard-framework.md)** - Compliance and regulatory standards

### Database

- **[Database Schema](database-schema.md)** - InfluxDB schema design and data organization

## 🏗️ System Architecture Overview

### Services

| Service | Technology | Port | Purpose |
|---------|-----------|------|---------|
| **websocket-ingestion** | Python/aiohttp | 8001 | Home Assistant WebSocket client |
| **enrichment-pipeline** | Python/FastAPI | 8002 | Data validation and weather enrichment |
| **data-retention** | Python/FastAPI | 8080 | Data lifecycle and cleanup management |
| **admin-api** | Python/FastAPI | 8003 | Administration REST API |
| **health-dashboard** | React/TypeScript | 3000 | Web-based monitoring interface |
| **weather-api** | Python/FastAPI | Internal | Weather data integration |
| **influxdb** | InfluxDB 2.7 | 8086 | Time-series data storage |

### Data Flow

```
Home Assistant → WebSocket Ingestion → Enrichment Pipeline → InfluxDB
                                           ↑
                                    Weather API
```

### Key Architectural Patterns

- **Microservices Architecture**: Independent, containerized services
- **Event-Driven Processing**: Real-time WebSocket event streaming
- **API Gateway Pattern**: FastAPI as unified REST interface
- **Service Isolation**: Docker containerization with health checks
- **Optimized Deployment**: Multi-stage Docker builds with Alpine Linux (71% size reduction)

## 📊 Technology Decisions

### Frontend Stack
- **React 18.2** + **TypeScript 5.2** - Type-safe UI development
- **TailwindCSS 3.4** - Utility-first styling
- **Vite 5.0** - Fast build tooling
- **Vitest 1.0** - Component testing

### Backend Stack
- **Python 3.11** - Async/await support
- **FastAPI 0.104** - High-performance REST APIs
- **aiohttp 3.9** - WebSocket client
- **pytest 7.4** - Backend testing

### Data & Infrastructure
- **InfluxDB 2.7** - Time-series database
- **Docker Compose 2.20+** - Service orchestration
- **Playwright 1.55** - E2E testing
- **GitHub Actions** - CI/CD pipeline

## 🔒 Security Architecture

- **Authentication**: Long-lived access tokens for Home Assistant
- **API Security**: API key authentication for admin endpoints
- **Container Security**: Non-root users, read-only filesystems
- **Network Security**: Internal service communication, minimal external ports

## 📈 Performance Characteristics

- **Event Processing**: 10,000+ events/day
- **Response Time**: <100ms API calls
- **Reliability**: 99.9% uptime with auto-reconnection
- **Container Size**: 71% reduction with Alpine images (40-80MB per service)

## 🧪 Testing Strategy

- **Unit Tests**: 600+ tests across services (pytest, Vitest)
- **Integration Tests**: End-to-end workflow testing
- **E2E Tests**: Playwright browser testing
- **Coverage Target**: 95%+ for critical services

## 🔍 Monitoring & Observability

- **Structured Logging**: JSON format with correlation IDs
- **Health Checks**: All services expose `/health` endpoints
- **Metrics Collection**: Real-time system and application metrics
- **Alerting**: Configurable thresholds for critical metrics

## 📖 Additional Documentation

### Project Documentation
- **[PRD](../prd.md)** - Product Requirements Document
- **[Stories](../stories/)** - User stories and epic documentation
- **[QA Gates](../qa/gates/)** - Quality assurance checkpoints

### Operational Documentation
- **[Deployment Guide](../DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- **[Production Deployment](../PRODUCTION_DEPLOYMENT.md)** - Production setup guide
- **[Security Configuration](../SECURITY_CONFIGURATION.md)** - Security best practices
- **[Troubleshooting Guide](../TROUBLESHOOTING_GUIDE.md)** - Common issues and solutions

### Developer Documentation
- **[API Documentation](../API_DOCUMENTATION.md)** - Complete API reference
- **[CLI Reference](../CLI_REFERENCE.md)** - Command-line tools
- **[User Manual](../USER_MANUAL.md)** - End-user documentation

### Integration Documentation
- **[Context7 Integration](../CONTEXT7_INTEGRATION.md)** - Context7 MCP integration guide
- **[Context7 KB Status](../kb/CONTEXT7_KB_STATUS_REPORT.md)** - Knowledge base status

## 🚀 Getting Started

1. **Read the [Introduction](introduction.md)** to understand the system
2. **Review the [Tech Stack](tech-stack.md)** for technology details
3. **Follow the [Development Workflow](development-workflow.md)** to set up your environment
4. **Check [Coding Standards](coding-standards.md)** before contributing

## 📝 Conventions

- All documentation uses Markdown format
- Code examples include language tags
- Architecture diagrams use Mermaid format where possible
- Links use relative paths from document location

## 🔄 Keeping Documentation Updated

This architecture documentation should be updated whenever:
- New services are added or removed
- Technology choices change
- Architectural patterns are introduced
- Performance characteristics change significantly

---

**Last Updated**: October 2025  
**Version**: 4.0  
**Status**: Production Ready  
**Maintained By**: HA Ingestor Team

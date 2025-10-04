# Technology Stack

This is the DEFINITIVE technology selection for the entire Home Assistant Ingestor project. Based on the PRD requirements and architectural analysis, here are the technology choices:

| Category | Technology | Version | Purpose | Rationale |
|----------|------------|---------|---------|-----------|
| **Frontend Language** | TypeScript | 5.2.2 | Type-safe frontend development | Type safety for shared data models and React components |
| **Frontend Framework** | React | 18.2.0 | Admin dashboard UI | Simple, proven UI framework with excellent ecosystem |
| **UI Component Library** | TailwindCSS | 3.4.0 | Utility-first CSS framework | Modern, responsive design system with excellent developer experience |
| **Icons** | Heroicons | 2.2.0 | Icon library | Consistent with TailwindCSS ecosystem |
| **State Management** | React Context + Hooks | 18.2.0 | Frontend state management | Built-in React state management for current scale |
| **Backend Language** | Python | 3.11 | WebSocket client and data processing | Simple, proven async support with excellent libraries |
| **Backend Framework (API)** | FastAPI | 0.104.1 | REST API for admin interface | High performance, automatic OpenAPI docs, excellent async support |
| **Backend Framework (WebSocket)** | aiohttp | 3.9.1 | WebSocket client + async HTTP | Native async WebSocket + simple HTTP API for real-time streaming |
| **API Style** | REST + WebSocket | - | Admin API + Real-time streaming | REST for admin interface, WebSocket for real-time data |
| **Database** | InfluxDB | 2.7 | Time-series data storage | Purpose-built for time-series data and Home Assistant events |
| **File Storage** | Local Docker Volumes | - | Persistent data storage | Simple local storage with Docker Compose |
| **Authentication** | Long-lived Access Tokens | - | Home Assistant authentication | HA's standard auth method for WebSocket connections |
| **Frontend Testing** | Vitest | 1.0.4 | Frontend component testing | Fast, Vite-native testing with excellent TypeScript support |
| **Backend Testing** | pytest | 7.4.3 | Backend service testing | Simple, comprehensive testing for Python services |
| **E2E Testing** | Playwright | 1.55.1 | End-to-end testing | Modern, reliable E2E testing for full application |
| **Build Tool** | Docker | 24+ | Containerization | Standard deployment with multi-stage builds |
| **Bundler** | Vite | 5.0.8 | Frontend build tool | Fast, simple build tool with excellent TypeScript support |
| **Orchestration** | Docker Compose | 2.20+ | Service orchestration | Simple orchestration for local deployment |
| **CI/CD** | GitHub Actions | - | Automated testing | Free CI/CD with Docker support |
| **Monitoring** | Python logging | - | Application logging | Built-in logging with structured JSON format |
| **Logging** | Python logging | - | Application logging | Standard logging with health check integration |

## Technology Rationale

### Frontend Stack
- **React + TypeScript**: Provides type safety and excellent developer experience for complex dashboard interfaces
- **TailwindCSS**: Utility-first approach enables rapid UI development with consistent design system
- **Vite**: Fast build tool with excellent TypeScript support and hot module replacement
- **Vitest**: Vite-native testing framework with Jest compatibility for familiar testing patterns

### Backend Stack
- **FastAPI**: High-performance async framework with automatic OpenAPI documentation
- **aiohttp**: Lightweight async HTTP library perfect for WebSocket connections to Home Assistant
- **Python 3.11**: Latest stable version with excellent async/await support and performance improvements

### Data & Storage
- **InfluxDB 2.7**: Purpose-built for time-series data, perfect for Home Assistant sensor data
- **Docker Volumes**: Simple, reliable local storage for development and production

### Testing Strategy
- **Vitest**: Fast, modern testing for React components with TypeScript support
- **pytest**: Comprehensive testing framework for Python services
- **Playwright**: Reliable E2E testing across multiple browsers

### Deployment
- **Docker Compose**: Simple orchestration for local development and production deployment
- **GitHub Actions**: Free CI/CD with Docker support for automated testing and deployment

## Version Management

All versions are pinned to ensure reproducible builds and consistent behavior across development and production environments. Dependencies are managed through:

- **Frontend**: `package.json` with exact version pinning
- **Backend**: `requirements.txt` with version constraints
- **Infrastructure**: Docker image tags with specific versions

## Future Technology Considerations

- **State Management**: Consider Redux Toolkit if state complexity grows
- **Database**: InfluxDB 2.7 provides excellent performance for current scale
- **Monitoring**: May add Prometheus/Grafana for advanced monitoring in future
- **Caching**: Redis could be added for API response caching if needed
